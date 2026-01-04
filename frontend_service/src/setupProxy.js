const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',  // ✅ Must be 8000, NOT 3000
      changeOrigin: true,
      pathRewrite: {
        '^/api': '/api'  // Keep /api prefix
      }
    })
  );
};