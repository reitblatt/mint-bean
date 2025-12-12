import { useState } from 'react'
import type { CategoryTreeNode } from '@/api/types'

interface CategoryTreeProps {
  nodes: CategoryTreeNode[]
  selectedId?: number
  onSelect?: (node: CategoryTreeNode) => void
  onEdit?: (node: CategoryTreeNode) => void
  onDelete?: (node: CategoryTreeNode) => void
  showTypeTag?: boolean
}

interface CategoryNodeProps {
  node: CategoryTreeNode
  level: number
  selectedId?: number
  onSelect?: (node: CategoryTreeNode) => void
  onEdit?: (node: CategoryTreeNode) => void
  onDelete?: (node: CategoryTreeNode) => void
  showTypeTag?: boolean
}

function CategoryNode({
  node,
  level,
  selectedId,
  onSelect,
  onEdit,
  onDelete,
  showTypeTag = true,
}: CategoryNodeProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const hasChildren = node.children && node.children.length > 0
  const isSelected = selectedId === node.id

  const categoryTypeColors: Record<string, string> = {
    expense: 'text-red-600 bg-red-50',
    income: 'text-green-600 bg-green-50',
    transfer: 'text-blue-600 bg-blue-50',
  }

  return (
    <div>
      <div
        className={`flex items-center py-2 px-3 rounded-lg hover:bg-gray-50 cursor-pointer ${
          isSelected ? 'bg-blue-50 ring-2 ring-blue-500' : ''
        }`}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        onClick={() => onSelect?.(node)}
      >
        {/* Expand/Collapse Arrow */}
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
            className="mr-2 text-gray-400 hover:text-gray-600"
          >
            {isExpanded ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </button>
        )}

        {/* Icon */}
        {node.icon ? (
          <span className="mr-2 text-lg">{node.icon}</span>
        ) : (
          <div className="w-5 h-5 mr-2" />
        )}

        {/* Category Name */}
        <div className="flex-1 flex items-center gap-3">
          <span className="font-medium text-gray-900">{node.display_name}</span>

          {/* Type Badge - only show if showTypeTag is true */}
          {showTypeTag && (
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                categoryTypeColors[node.category_type] || 'text-gray-600 bg-gray-100'
              }`}
            >
              {node.category_type}
            </span>
          )}

          {/* Transaction Count */}
          {node.transaction_count > 0 && (
            <span className="text-sm text-gray-500">
              {node.transaction_count} transaction{node.transaction_count !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-1 ml-2" onClick={(e) => e.stopPropagation()}>
          {onEdit && (
            <button
              onClick={() => onEdit(node)}
              className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
              title="Edit category"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(node)}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
              title="Delete category"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <CategoryNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              onEdit={onEdit}
              onDelete={onDelete}
              showTypeTag={showTypeTag}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function CategoryTree({
  nodes,
  selectedId,
  onSelect,
  onEdit,
  onDelete,
  showTypeTag = true,
}: CategoryTreeProps) {
  if (!nodes || nodes.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No categories found</p>
        <p className="text-sm mt-2">Create your first category to get started</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {nodes.map((node) => (
        <CategoryNode
          key={node.id}
          node={node}
          level={0}
          selectedId={selectedId}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
          showTypeTag={showTypeTag}
        />
      ))}
    </div>
  )
}
