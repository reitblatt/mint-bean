export default function Settings() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      <div className="max-w-2xl space-y-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Beancount Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beancount File Path
              </label>
              <input type="text" className="input" placeholder="/path/to/main.beancount" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Repository Path
              </label>
              <input type="text" className="input" placeholder="/path/to/beancount/repo" />
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Plaid Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Environment
              </label>
              <select className="input">
                <option value="sandbox">Sandbox</option>
                <option value="development">Development</option>
                <option value="production">Production</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button className="btn btn-primary">Save Settings</button>
        </div>
      </div>
    </div>
  )
}
