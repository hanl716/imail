const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '^/api': { // This will match requests starting with /api
        target: 'http://localhost:8000', // Your FastAPI backend URL
        changeOrigin: true,
        // pathRewrite: {'^/api' : '/api/v1'} // Example: if backend expects /api/v1 but frontend calls /api
                                            // In our case, frontend calls include /api/v1/auth, so this is not needed.
                                            // The target should be the base URL of the backend.
      }
    }
  }
})
