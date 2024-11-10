module.exports = {
  content: [
    "./*.html", // Quét tất cả các file HTML trong thư mục gốc
    "./src/**/*.html", // Quét tất cả các file HTML trong thư mục src
    "./src/**/*.js", // Quét các file JavaScript trong thư mục src
    "./src/**/*.jsx", // Nếu bạn sử dụng React
    "./src/**/*.vue", // Nếu bạn sử dụng Vue
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
