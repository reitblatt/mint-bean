import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { rulesApi } from '@/api/rules'
import { categoriesApi } from '@/api/categories'
import type { Rule } from '@/api/types'

interface RuleFormModalProps {
  isOpen: boolean
  onClose: () => void
  rule?: Rule
}

type ConditionOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'not_contains'
  | 'starts_with'
  | 'ends_with'
  | 'regex'
  | 'greater_than'
  | 'less_than'

interface SimpleCondition {
  field: string
  operator: ConditionOperator
  value: string
}

export default function RuleFormModal({ isOpen, onClose, rule }: RuleFormModalProps) {
  const queryClient = useQueryClient()
  const isEdit = !!rule

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState(0)
  const [active, setActive] = useState(true)
  const [categoryId, setCategoryId] = useState<number | undefined>()

  // Simplified condition builder - single condition for now
  const [conditionField, setConditionField] = useState('description')
  const [conditionOperator, setConditionOperator] = useState<ConditionOperator>('contains')
  const [conditionValue, setConditionValue] = useState('')

  // Fetch categories for dropdown
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list(),
  })

  useEffect(() => {
    if (rule) {
      setName(rule.name)
      setDescription(rule.description || '')
      setPriority(rule.priority)
      setActive(rule.active)
      setCategoryId(rule.category_id)

      // Parse conditions (simplified - just handle single condition)
      if (rule.conditions && typeof rule.conditions === 'object') {
        const cond = rule.conditions as unknown as SimpleCondition
        if (cond.field) {
          setConditionField(cond.field)
          setConditionOperator(cond.operator)
          setConditionValue(cond.value || '')
        }
      }
    } else {
      setName('')
      setDescription('')
      setPriority(0)
      setActive(true)
      setCategoryId(undefined)
      setConditionField('description')
      setConditionOperator('contains')
      setConditionValue('')
    }
  }, [rule, isOpen])

  const createMutation = useMutation({
    mutationFn: rulesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      onClose()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: { id: number; updates: Partial<Rule> }) =>
      rulesApi.update(data.id, data.updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Build conditions object
    const conditions: SimpleCondition = {
      field: conditionField,
      operator: conditionOperator,
      value: conditionValue,
    }

    // Build actions object
    const actions: Record<string, unknown> = {}
    if (categoryId) {
      actions.set_category = categoryId
    }

    const ruleData = {
      name,
      description,
      conditions: conditions as unknown as Record<string, unknown>,
      actions,
      priority,
      active,
      category_id: categoryId,
    }

    if (isEdit && rule) {
      updateMutation.mutate({ id: rule.id, updates: ruleData })
    } else {
      createMutation.mutate(ruleData)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {isEdit ? 'Edit Rule' : 'Create Rule'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name *</label>
              <input
                type="text"
                required
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Auto-categorize Amazon purchases"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                className="input"
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
              />
            </div>

            {/* Condition Builder */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Condition</h3>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Field</label>
                  <select
                    className="input text-sm"
                    value={conditionField}
                    onChange={(e) => setConditionField(e.target.value)}
                  >
                    <option value="description">Description</option>
                    <option value="payee">Payee</option>
                    <option value="amount">Amount</option>
                    <option value="account.name">Account Name</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Operator</label>
                  <select
                    className="input text-sm"
                    value={conditionOperator}
                    onChange={(e) => setConditionOperator(e.target.value as ConditionOperator)}
                  >
                    <option value="contains">Contains</option>
                    <option value="not_contains">Does not contain</option>
                    <option value="equals">Equals</option>
                    <option value="not_equals">Not equals</option>
                    <option value="starts_with">Starts with</option>
                    <option value="ends_with">Ends with</option>
                    <option value="regex">Regex match</option>
                    <option value="greater_than">Greater than</option>
                    <option value="less_than">Less than</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Value</label>
                  <input
                    type="text"
                    required
                    className="input text-sm"
                    value={conditionValue}
                    onChange={(e) => setConditionValue(e.target.value)}
                    placeholder="Value to match"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Example: If description contains "amazon", assign to category
              </p>
            </div>

            {/* Action - Category Assignment */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Assign to Category *
              </label>
              <select
                required
                className="input"
                value={categoryId || ''}
                onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
              >
                <option value="">Select a category...</option>
                {categories?.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.icon} {cat.display_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority & Active */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <input
                  type="number"
                  className="input"
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 mt-1">Higher priority rules run first</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <div className="flex items-center h-10">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      checked={active}
                      onChange={(e) => setActive(e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">Active</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                className="btn btn-primary flex-1"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {createMutation.isPending || updateMutation.isPending
                  ? 'Saving...'
                  : isEdit
                    ? 'Update Rule'
                    : 'Create Rule'}
              </button>
              <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
                Cancel
              </button>
            </div>

            {/* Error */}
            {(createMutation.isError || updateMutation.isError) && (
              <div className="text-sm text-red-600 mt-2">
                Error: {(createMutation.error || updateMutation.error)?.message}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}
