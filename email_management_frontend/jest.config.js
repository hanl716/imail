module.exports = {
  preset: '@vue/cli-plugin-unit-jest/presets/babel', // Using babel preset for JS projects
  transform: {
    '^.+\\.vue$': '@vue/vue3-jest',
    // Jest uses babel-jest for .js files by default with the preset.
    // If you have specific JS transformation needs (e.g. for ES modules in node_modules),
    // you might need to adjust transformIgnorePatterns or add babel-jest explicitly here for .js/.jsx.
  },
  moduleFileExtensions: ['js', 'json', 'vue'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1', // Map @/ to src/ directory
  },
  // testEnvironment: 'jsdom', // jsdom is default with jest preset for Vue
  // collectCoverage: true, // Optional: if you want coverage reports
  // collectCoverageFrom: [ // Optional: configure coverage sources
  //   'src/**/*.{js,vue}',
  //   '!src/main.js', // No need to cover bootstrap file
  //   '!src/router/index.js', // Router config often tested via e2e
  //   '!src/stores/index.js', // If it's just an aggregation of stores
  //   // Add other exclusions as needed
  // ],
  // setupFilesAfterEnv: ['<rootDir>/tests/unit/setup.js'], // If you need global setup
};
