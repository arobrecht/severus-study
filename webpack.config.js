const path = require('path');

module.exports = {
    entry: './severusStudy/src/main.ts',
    mode: "production",
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
    },
    output: {
        filename: 'main.js',
        path: path.resolve(__dirname, 'severusStudy/static/js'),
        globalObject: 'this',
        library: {
            name: 'study',
            type: 'umd',
        },
    },
};
