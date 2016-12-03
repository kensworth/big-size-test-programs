'use strict';
const _eval = require('eval');

const testCases = {
    1: 1,
    2: 1,
    3: 2,
    4: 3,
    5: 5,
    6: 8
};

const useStrict = `
    'use strict';
`;

const s = `
    const fib = (n) => {
        if (n < 1) {
            return null;
        }
        const fibMatrix = [null] * (n + 1);
        fibMatrix[0] = 1;
        fibMatrix[1] = 1;
        for (let i = 2; i < n; i++) {
            fibMatrix[i] = fibMatrix[i - 1] + fibMatrix[i - 2];
        } 
        return fibMatrix[n - 1];
    };
`;

const exports = ex

const executable = useStrict + s + exportFunction;
const fib = _eval(executable);
console.log(fib(1));
