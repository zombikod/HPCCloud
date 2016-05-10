module.exports = {
  extends: 'airbnb',
  rules: {
    'max-len': [1, 160, 4, {"ignoreUrls": true}],
    'no-console': 0,
    'no-multi-spaces': [2, { exceptions: { "ImportDeclaration": true } }],
    'no-nested-ternary': 0,
    'no-param-reassign': [2, { props: false }],
    'no-unused-vars': [2, { args: 'none' }],
    'no-var': 0,
    'no-underscore-dangle': 0,
    'one-var': 0,
    'block-spacing': 0,
    'global-require': 0,
    'import/no-unresolved': 0,
    'react/no-is-mounted': 1,
    'react/prefer-es6-class': 0,
    'react/prefer-stateless-function': 0,
    'react/jsx-curly-spacing': 0,
    'react/jsx-first-prop-new-line': 0,
    'react/jsx-indent': 0,
    'jsx-a11y/img-has-alt': 0,
  }
};
