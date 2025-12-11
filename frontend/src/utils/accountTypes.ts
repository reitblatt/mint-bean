/**
 * Utility functions for account type display and categorization
 */

export interface AccountTypeInfo {
  displayName: string
  icon: string
  category: 'depository' | 'credit' | 'investment' | 'loan' | 'other'
}

/**
 * Get display information for an account based on its type and subtype
 */
export function getAccountTypeInfo(type: string, subtype?: string | null): AccountTypeInfo {
  // Handle specific subtypes first
  if (subtype) {
    const subtypeLower = subtype.toLowerCase()

    // Depository accounts
    if (subtypeLower === 'checking') {
      return { displayName: 'Checking', icon: '💳', category: 'depository' }
    }
    if (subtypeLower === 'savings') {
      return { displayName: 'Savings', icon: '🏦', category: 'depository' }
    }
    if (subtypeLower === 'cd') {
      return { displayName: 'CD', icon: '💿', category: 'depository' }
    }
    if (subtypeLower === 'money market') {
      return { displayName: 'Money Market', icon: '📊', category: 'depository' }
    }
    if (subtypeLower === 'paypal') {
      return { displayName: 'PayPal', icon: '💰', category: 'depository' }
    }
    if (subtypeLower === 'prepaid') {
      return { displayName: 'Prepaid', icon: '💵', category: 'depository' }
    }
    if (subtypeLower === 'cash management') {
      return { displayName: 'Cash Management', icon: '💼', category: 'depository' }
    }
    if (subtypeLower === 'ebt') {
      return { displayName: 'EBT', icon: '🎫', category: 'depository' }
    }

    // Credit accounts
    if (subtypeLower === 'credit card') {
      return { displayName: 'Credit Card', icon: '💳', category: 'credit' }
    }
    if (subtypeLower === 'line of credit') {
      return { displayName: 'Line of Credit', icon: '💼', category: 'credit' }
    }

    // Investment accounts
    if (subtypeLower === '401k') {
      return { displayName: '401(k)', icon: '🏦', category: 'investment' }
    }
    if (subtypeLower === '403b') {
      return { displayName: '403(b)', icon: '🏦', category: 'investment' }
    }
    if (subtypeLower === '457b') {
      return { displayName: '457(b)', icon: '🏦', category: 'investment' }
    }
    if (subtypeLower === 'ira') {
      return { displayName: 'IRA', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'roth') {
      return { displayName: 'Roth IRA', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'roth 401k') {
      return { displayName: 'Roth 401(k)', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'rollover ira') {
      return { displayName: 'Rollover IRA', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'sep ira') {
      return { displayName: 'SEP IRA', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'simple ira') {
      return { displayName: 'SIMPLE IRA', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'brokerage') {
      return { displayName: 'Brokerage', icon: '📈', category: 'investment' }
    }
    if (subtypeLower === 'cash isa') {
      return { displayName: 'Cash ISA', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'education savings account') {
      return { displayName: 'Education Savings', icon: '🎓', category: 'investment' }
    }
    if (subtypeLower === 'fixed annuity') {
      return { displayName: 'Fixed Annuity', icon: '📊', category: 'investment' }
    }
    if (subtypeLower === 'gic') {
      return { displayName: 'GIC', icon: '💼', category: 'investment' }
    }
    if (subtypeLower === 'health reimbursement arrangement') {
      return { displayName: 'HRA', icon: '🏥', category: 'investment' }
    }
    if (subtypeLower === 'hsa') {
      return { displayName: 'HSA', icon: '🏥', category: 'investment' }
    }
    if (subtypeLower === 'investment') {
      return { displayName: 'Investment', icon: '📈', category: 'investment' }
    }
    if (subtypeLower === 'keogh') {
      return { displayName: 'Keogh', icon: '💼', category: 'investment' }
    }
    if (subtypeLower === 'lif') {
      return { displayName: 'LIF', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'lira') {
      return { displayName: 'LIRA', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'lrif') {
      return { displayName: 'LRIF', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'lrsp') {
      return { displayName: 'LRSP', icon: '💼', category: 'investment' }
    }
    if (subtypeLower === 'mutual fund') {
      return { displayName: 'Mutual Fund', icon: '📊', category: 'investment' }
    }
    if (subtypeLower === 'non-taxable brokerage account') {
      return { displayName: 'Non-Taxable Brokerage', icon: '📈', category: 'investment' }
    }
    if (subtypeLower === 'pension') {
      return { displayName: 'Pension', icon: '🏛️', category: 'investment' }
    }
    if (subtypeLower === 'plan') {
      return { displayName: 'Retirement Plan', icon: '📋', category: 'investment' }
    }
    if (subtypeLower === 'prif') {
      return { displayName: 'PRIF', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'profit sharing plan') {
      return { displayName: 'Profit Sharing', icon: '💼', category: 'investment' }
    }
    if (subtypeLower === 'rdsp') {
      return { displayName: 'RDSP', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'resp') {
      return { displayName: 'RESP', icon: '🎓', category: 'investment' }
    }
    if (subtypeLower === 'retirement') {
      return { displayName: 'Retirement', icon: '🏖️', category: 'investment' }
    }
    if (subtypeLower === 'rlif') {
      return { displayName: 'RLIF', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'rrif') {
      return { displayName: 'RRIF', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'rrsp') {
      return { displayName: 'RRSP', icon: '🎯', category: 'investment' }
    }
    if (subtypeLower === 'sarsep') {
      return { displayName: 'SARSEP', icon: '💼', category: 'investment' }
    }
    if (subtypeLower === 'stock plan') {
      return { displayName: 'Stock Plan', icon: '📊', category: 'investment' }
    }
    if (subtypeLower === 'tfsa') {
      return { displayName: 'TFSA', icon: '💰', category: 'investment' }
    }
    if (subtypeLower === 'thrift savings plan') {
      return { displayName: 'TSP', icon: '💼', category: 'investment' }
    }
    if (subtypeLower === 'trust') {
      return { displayName: 'Trust', icon: '🏛️', category: 'investment' }
    }
    if (subtypeLower === 'ugma') {
      return { displayName: 'UGMA', icon: '👶', category: 'investment' }
    }
    if (subtypeLower === 'utma') {
      return { displayName: 'UTMA', icon: '👶', category: 'investment' }
    }
    if (subtypeLower === 'variable annuity') {
      return { displayName: 'Variable Annuity', icon: '📊', category: 'investment' }
    }

    // Loan accounts
    if (subtypeLower === 'auto') {
      return { displayName: 'Auto Loan', icon: '🚗', category: 'loan' }
    }
    if (subtypeLower === 'commercial') {
      return { displayName: 'Commercial Loan', icon: '🏢', category: 'loan' }
    }
    if (subtypeLower === 'construction') {
      return { displayName: 'Construction Loan', icon: '🏗️', category: 'loan' }
    }
    if (subtypeLower === 'consumer') {
      return { displayName: 'Consumer Loan', icon: '💰', category: 'loan' }
    }
    if (subtypeLower === 'home equity') {
      return { displayName: 'Home Equity', icon: '🏠', category: 'loan' }
    }
    if (subtypeLower === 'loan') {
      return { displayName: 'Loan', icon: '💵', category: 'loan' }
    }
    if (subtypeLower === 'mortgage') {
      return { displayName: 'Mortgage', icon: '🏡', category: 'loan' }
    }
    if (subtypeLower === 'overdraft') {
      return { displayName: 'Overdraft', icon: '⚠️', category: 'loan' }
    }
    if (subtypeLower === 'student') {
      return { displayName: 'Student Loan', icon: '🎓', category: 'loan' }
    }
  }

  // Fall back to type if subtype not recognized
  const typeLower = type.toLowerCase()

  if (typeLower === 'depository') {
    return { displayName: 'Depository', icon: '🏦', category: 'depository' }
  }
  if (typeLower === 'credit') {
    return { displayName: 'Credit', icon: '💳', category: 'credit' }
  }
  if (typeLower === 'investment') {
    return { displayName: 'Investment', icon: '📈', category: 'investment' }
  }
  if (typeLower === 'loan') {
    return { displayName: 'Loan', icon: '💵', category: 'loan' }
  }
  if (typeLower === 'other') {
    return { displayName: 'Other', icon: '📁', category: 'other' }
  }

  // Default fallback
  return { displayName: type, icon: '📁', category: 'other' }
}

/**
 * Format last sync time for display
 */
export function formatLastSync(lastSyncedAt: string | null): string {
  if (!lastSyncedAt) {
    return 'Never synced'
  }

  const date = new Date(lastSyncedAt)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) {
    return 'Just now'
  }
  if (diffMins < 60) {
    return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`
  }
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`
  }
  if (diffDays < 7) {
    return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
  }

  return date.toLocaleDateString()
}
