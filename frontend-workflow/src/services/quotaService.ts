import { backendFetch } from './backendClient';
import { fetchRuntimeConfig, getRuntimeConfigSync } from './runtimeConfigService';

export interface QuotaInfo {
  used: number;
  limit: number;
  remaining: number;
  isAuthenticated: boolean;
  billingMode?: string;
}

export interface RecordUsageOptions {
  amount?: number;
  // Kept only for backward-compatible call sites. Guest mode has been removed.
  isAnonymous?: boolean;
}

function buildUnlimitedQuota(): QuotaInfo {
  return {
    used: 0,
    limit: Number.MAX_SAFE_INTEGER,
    remaining: Number.MAX_SAFE_INTEGER,
    isAuthenticated: false,
    billingMode: getRuntimeConfigSync().billing_mode,
  };
}

/**
 * Check current quota for the active deployment mode.
 *
 * - With Supabase configured, quota comes from the authenticated account.
 * - Without Supabase, backend returns unlimited local usage.
 */
export async function checkQuota(userId: string | null, _legacyIsAnonymous: boolean = false): Promise<QuotaInfo> {
  await fetchRuntimeConfig().catch(() => undefined);
  try {
    const response = await backendFetch('/api/v1/account/quota');
    if (!response.ok) {
      console.warn('[quotaService] Quota request failed:', response.status);
      return buildUnlimitedQuota();
    }
    const data = await response.json();
    return {
      used: Number(data.used || 0),
      limit: Number(data.limit || 0),
      remaining: Number(data.remaining || 0),
      isAuthenticated: Boolean(data.is_authenticated),
      billingMode: data.billing_mode || getRuntimeConfigSync().billing_mode,
    };
  } catch (err) {
    console.error('[quotaService] Error checking quota:', err);
    return buildUnlimitedQuota();
  }
}

/**
 * Record a workflow usage.
 *
 * @param userId - Supabase user ID if logged in
 * @param workflowType - Type of workflow used (e.g., 'paper2figure')
 * @returns true if recorded successfully
 */
export async function recordUsage(
  userId: string | null,
  workflowType: string,
  options: RecordUsageOptions = {}
): Promise<boolean> {
  await fetchRuntimeConfig().catch(() => undefined);
  if (getRuntimeConfigSync().server_side_billing_enforced) {
    return true;
  }

  const amount = Math.max(1, options.amount ?? 1);

  try {
    const response = await backendFetch('/api/v1/account/quota/consume', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        workflow_type: workflowType,
        amount,
      }),
    });
    if (!response.ok) {
      console.warn('[quotaService] Failed to consume quota:', response.status);
      return false;
    }
    return true;
  } catch (err) {
    console.error('[quotaService] Error recording usage:', err);
    return false;
  }
}

/**
 * Check if user has remaining quota.
 *
 * @param userId - Supabase user ID if logged in
 * @returns true if user has remaining quota
 */
export async function hasQuota(userId: string | null): Promise<boolean> {
  const quota = await checkQuota(userId);
  return quota.remaining > 0;
}
