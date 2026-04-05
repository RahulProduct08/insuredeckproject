import React, { useEffect } from 'react'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import DetailPanel from '../components/DetailPanel.jsx'

const COLUMNS = [
  { key: 'name', label: 'Product' },
  { key: 'min_premium', label: 'Min Premium', render: (v) => `₹${Number(v).toLocaleString('en-IN')}` },
  { key: 'max_premium', label: 'Max Premium', render: (v) => `₹${Number(v).toLocaleString('en-IN')}` },
  { key: 'commission_rate_percent', label: 'Commission %', render: (v) => `${v}%` },
  {
    key: 'is_active', label: 'Status',
    render: (v) => (
      <span className={`inline-flex items-center gap-1 text-xs font-medium ${v ? 'text-green-700' : 'text-slate-400'}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${v ? 'bg-green-500' : 'bg-slate-300'}`} />
        {v ? 'Active' : 'Inactive'}
      </span>
    ),
  },
]

const DETAIL_FIELDS = [
  { key: 'name', label: 'Product Name', editable: true },
  { key: 'description', label: 'Description', editable: true, type: 'textarea' },
  { key: 'min_premium', label: 'Min Premium (₹)', editable: true, type: 'number', currency: true },
  { key: 'max_premium', label: 'Max Premium (₹)', editable: true, type: 'number', currency: true },
  { key: 'min_age', label: 'Min Age (years)', editable: true, type: 'number' },
  { key: 'max_age', label: 'Max Age (years)', editable: true, type: 'number' },
  { key: 'min_income', label: 'Min Income (₹)', editable: true, type: 'number', currency: true },
  { key: 'commission_rate_percent', label: 'Commission Rate (%)', editable: true, type: 'number' },
]

export default function Products() {
  const { products, fetchProducts, productsLoading, selectedProduct, setSelectedProduct, updateProduct } = useStore()

  useEffect(() => {
    fetchProducts()
  }, [])

  const handleSave = async (patch) => {
    await updateProduct(selectedProduct.product_id, patch)
    fetchProducts()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
        <h1 className="text-xl font-semibold text-slate-900">Products</h1>
        <p className="text-sm text-slate-500">{products.length} products in catalog</p>
      </div>

      {/* Main */}
      <div className="flex-1 flex overflow-hidden">
        <div className={`flex flex-col overflow-hidden ${selectedProduct ? 'w-3/5' : 'w-full'}`}>
          <DataTable
            columns={COLUMNS}
            data={products}
            loading={productsLoading}
            rowKey="product_id"
            searchKeys={['name', 'description']}
            onRowClick={setSelectedProduct}
            selected={selectedProduct}
            emptyText="No products in catalog."
          />
        </div>

        {selectedProduct && (
          <div className="w-2/5 flex flex-col overflow-hidden">
            <DetailPanel
              title={selectedProduct.name}
              item={selectedProduct}
              fields={DETAIL_FIELDS}
              onSave={handleSave}
              onClose={() => setSelectedProduct(null)}
            />
          </div>
        )}
      </div>
    </div>
  )
}
