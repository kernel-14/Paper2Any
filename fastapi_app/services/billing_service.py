from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException

from fastapi_app.config.pricing import get_pricing_config, get_workflow_cost
from fastapi_app.dependencies import AuthUser
from fastapi_app.services.guest_quota_service import GuestQuotaService
from fastapi_app.services.managed_api_service import get_runtime_billing_config, is_free_billing_mode
from fastapi_app.services.supabase_admin_service import extract_response_data, get_supabase_admin_client


class BillingService:
    def __init__(self) -> None:
        self.guest_quota_service = GuestQuotaService()

    def _pricing(self) -> dict:
        return get_pricing_config()

    def _billing_config(self) -> dict:
        return self._pricing().get("billing", {})

    def _supabase(self):
        client = get_supabase_admin_client()
        if client is None:
            raise HTTPException(
                status_code=503,
                detail="Supabase service-role configuration is required for account and billing APIs",
            )
        return client

    def _select_many(
        self,
        table: str,
        columns: str,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = self._supabase().table(table).select(columns)
        for key, value in (filters or {}).items():
            query = query.eq(key, value)
        if order_by:
            query = query.order(order_by, desc=not ascending)
        if limit is not None:
            query = query.limit(limit)
        data = extract_response_data(query.execute()) or []
        return data if isinstance(data, list) else []

    def _select_first(self, table: str, columns: str, **filters: Any) -> Optional[Dict[str, Any]]:
        rows = self._select_many(table, columns, filters=filters, limit=1)
        return rows[0] if rows else None

    def _insert_row(self, table: str, payload: Dict[str, Any]) -> Any:
        return self._supabase().table(table).insert(payload).execute()

    def _generate_invite_code(self) -> str:
        for _ in range(12):
            candidate = uuid4().hex[:8].upper()
            if not self._select_first("profiles", "user_id", invite_code=candidate):
                return candidate
        raise HTTPException(status_code=500, detail="Failed to allocate invite code")

    def _ensure_profile(self, user: AuthUser) -> None:
        existing = self._select_first("profiles", "user_id, invite_code", user_id=user.id)
        if existing:
            return
        self._insert_row(
            "profiles",
            {
                "user_id": user.id,
                "invite_code": self._generate_invite_code(),
            },
        )

    def _append_ledger(
        self,
        *,
        user_id: str,
        points: int,
        reason: str,
        event_key: Optional[str] = None,
    ) -> None:
        payload = {
            "user_id": user_id,
            "points": int(points),
            "reason": reason,
        }
        if event_key:
            payload["event_key"] = event_key
        self._insert_row("points_ledger", payload)

    def _ensure_signup_bonus(self, user: AuthUser) -> None:
        signup_bonus_points = int(self._billing_config().get("signup_bonus_points", 20))
        if signup_bonus_points <= 0:
            return
        event_key = f"signup_bonus_{user.id}"
        existing = self._select_first("points_ledger", "id", event_key=event_key)
        if existing:
            return
        self._append_ledger(
            user_id=user.id,
            points=signup_bonus_points,
            reason="signup_bonus",
            event_key=event_key,
        )

    def _bootstrap_user(self, user: AuthUser) -> None:
        self._ensure_profile(user)
        self._ensure_signup_bonus(user)

    def _get_balance(self, user_id: str) -> int:
        balance_row = self._select_first("points_balance", "user_id, balance", user_id=user_id)
        if not balance_row:
            return 0
        try:
            return int(balance_row.get("balance", 0) or 0)
        except (TypeError, ValueError):
            return 0

    def _grant_daily_points_if_needed(self, user: AuthUser) -> None:
        billing = self._billing_config()
        daily_points = int(billing.get("daily_grant_points", 10))
        balance_cap = int(billing.get("daily_grant_balance_cap", 30))
        if daily_points <= 0:
            return

        current_balance = self._get_balance(user.id)
        if current_balance > balance_cap:
            return

        today = self.guest_quota_service.today()
        event_key = f"daily_grant_{today}_{user.id}"
        existing = self._select_first("points_ledger", "id", event_key=event_key)
        if existing:
            return

        self._append_ledger(
            user_id=user.id,
            points=daily_points,
            reason="daily_grant",
            event_key=event_key,
        )

    def _quota_from_guest(self, guest_id: Optional[str]) -> Dict[str, Any]:
        if not guest_id:
            raise HTTPException(status_code=400, detail="Unable to determine anonymous quota bucket")

        daily_limit = int(self._billing_config().get("guest_daily_limit", 15))
        used = self.guest_quota_service.get_usage(guest_id)
        remaining = max(0, daily_limit - used)
        return {
            "used": used,
            "limit": daily_limit,
            "remaining": remaining,
            "is_authenticated": False,
            "billing_mode": get_runtime_billing_config()["billing_mode"],
            "guest_id": guest_id,
        }

    def _quota_from_user(self, user: AuthUser) -> Dict[str, Any]:
        self._bootstrap_user(user)

        if not is_free_billing_mode():
            unlimited = 9_999_999
            return {
                "used": 0,
                "limit": unlimited,
                "remaining": unlimited,
                "is_authenticated": True,
                "billing_mode": "paid",
                "user_id": user.id,
            }

        self._grant_daily_points_if_needed(user)
        balance = self._get_balance(user.id)
        return {
            "used": 0,
            "limit": balance,
            "remaining": balance,
            "is_authenticated": True,
            "billing_mode": "free",
            "user_id": user.id,
        }

    def get_runtime_config(self) -> Dict[str, Any]:
        return get_runtime_billing_config()

    def get_quota(self, *, user: Optional[AuthUser], guest_id: Optional[str]) -> Dict[str, Any]:
        if user and not getattr(user, "is_anonymous", False):
            return self._quota_from_user(user)
        if user and getattr(user, "is_anonymous", False) and not guest_id:
            guest_id = user.id
        return self._quota_from_guest(guest_id)

    def consume_workflow(
        self,
        *,
        workflow_type: str,
        user: Optional[AuthUser],
        guest_id: Optional[str],
        amount: Optional[int] = None,
        event_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        requested_amount = max(1, int(amount or get_workflow_cost(workflow_type, default=1)))
        if user and getattr(user, "is_anonymous", False) and not guest_id:
            guest_id = user.id

        if user and not getattr(user, "is_anonymous", False):
            if not is_free_billing_mode():
                return {
                    "success": True,
                    "workflow_type": workflow_type,
                    "amount": 0,
                    "remaining": None,
                    "billing_mode": "paid",
                }

            self._bootstrap_user(user)
            self._grant_daily_points_if_needed(user)
            if event_key and self._select_first("points_ledger", "id", event_key=event_key):
                remaining = self._get_balance(user.id)
                return {
                    "success": True,
                    "workflow_type": workflow_type,
                    "amount": 0,
                    "remaining": remaining,
                    "billing_mode": "free",
                    "deduplicated": True,
                }
            balance = self._get_balance(user.id)
            if balance < requested_amount:
                raise HTTPException(status_code=402, detail="Insufficient points")
            self._append_ledger(
                user_id=user.id,
                points=-requested_amount,
                reason=f"workflow_{workflow_type}",
                event_key=event_key or f"workflow_{workflow_type}_{user.id}_{uuid4().hex}",
            )
            remaining = self._get_balance(user.id)
            return {
                "success": True,
                "workflow_type": workflow_type,
                "amount": requested_amount,
                "remaining": remaining,
                "billing_mode": "free",
            }

        quota = self._quota_from_guest(guest_id)
        if quota["remaining"] < requested_amount:
            raise HTTPException(status_code=402, detail="Guest trial quota exceeded")
        used = self.guest_quota_service.consume(guest_id or "", requested_amount)
        remaining = max(0, quota["limit"] - used)
        return {
            "success": True,
            "workflow_type": workflow_type,
            "amount": requested_amount,
            "remaining": remaining,
            "billing_mode": quota["billing_mode"],
            "guest_id": guest_id,
        }

    def get_account_profile(self, user: AuthUser) -> Dict[str, Any]:
        if getattr(user, "is_anonymous", False):
            raise HTTPException(status_code=400, detail="Anonymous users do not have an account profile")

        self._bootstrap_user(user)
        if is_free_billing_mode():
            self._grant_daily_points_if_needed(user)

        profile = self._select_first("profiles", "user_id, invite_code, created_at, updated_at", user_id=user.id) or {}
        referrals = self._select_many(
            "referrals",
            "id, inviter_user_id, invitee_user_id, invite_code, created_at",
            filters={"inviter_user_id": user.id},
            order_by="created_at",
            limit=20,
        )
        ledger = self._select_many(
            "points_ledger",
            "id, points, reason, event_key, created_at",
            filters={"user_id": user.id},
            order_by="created_at",
            limit=50,
        )

        return {
            "billing_mode": get_runtime_billing_config()["billing_mode"],
            "profile": profile,
            "points": {"balance": self._get_balance(user.id)},
            "referrals": referrals,
            "points_ledger": ledger,
            "pricing": self._pricing(),
        }

    def claim_invite_code(self, *, user: AuthUser, invite_code: str) -> Dict[str, Any]:
        if getattr(user, "is_anonymous", False):
            raise HTTPException(status_code=400, detail="Anonymous users cannot claim invite codes")

        normalized_code = (invite_code or "").strip().upper()
        if not normalized_code:
            raise HTTPException(status_code=400, detail="invite_code is required")

        self._bootstrap_user(user)

        existing_referral = self._select_first("referrals", "id", invitee_user_id=user.id)
        if existing_referral:
            raise HTTPException(status_code=409, detail="Invite code already claimed")

        inviter_profile = self._select_first("profiles", "user_id, invite_code", invite_code=normalized_code)
        if not inviter_profile:
            raise HTTPException(status_code=404, detail="Invalid invite code")

        inviter_user_id = str(inviter_profile.get("user_id", "") or "")
        if inviter_user_id == user.id:
            raise HTTPException(status_code=400, detail="Cannot claim your own invite code")

        self._insert_row(
            "referrals",
            {
                "inviter_user_id": inviter_user_id,
                "invitee_user_id": user.id,
                "invite_code": normalized_code,
            },
        )

        inviter_points = int(self._billing_config().get("referral_inviter_points", 5))
        invitee_points = int(self._billing_config().get("referral_invitee_points", 0))

        if inviter_points > 0:
            self._append_ledger(
                user_id=inviter_user_id,
                points=inviter_points,
                reason="referral_inviter",
                event_key=f"referral_inviter_{inviter_user_id}_{user.id}",
            )
        if invitee_points > 0:
            self._append_ledger(
                user_id=user.id,
                points=invitee_points,
                reason="referral_invitee",
                event_key=f"referral_invitee_{user.id}_{normalized_code}",
            )

        return {
            "success": True,
            "invite_code": normalized_code,
            "inviter_user_id": inviter_user_id,
            "inviter_reward_points": inviter_points,
            "invitee_reward_points": invitee_points,
            "remaining": self._get_balance(user.id),
        }
