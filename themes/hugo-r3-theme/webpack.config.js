const path = require("path");

<<<<<<< HEAD
module.exports = [{
    entry: {
        app: ["./scripts", "./styles/scss/main.scss"],
        vendor: "./scripts/vendor"
    },
    output: {
        path: path.resolve(__dirname, "./static/"),
        filename: "js/[name].js"
    },
    devtool: "source-map",
    module: {
        rules: [{
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: ["babel-loader", "eslint-loader"]
            },
            {
                test: /\.scss$/,
                use: [{
                        loader: "file-loader",
                        options: {
                            name: "css/[name].css"
=======
module.exports = [
    {
        entry: {
            app: ["./scripts", "./styles/scss/main.scss"],
            vendor: "./scripts/vendor"
        },
        output: {
            path: path.resolve(__dirname, "./static/"),
            filename: "js/[name].js"
        },
        devtool: "source-map",
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    exclude: /node_modules/,
                    use: ["babel-loader", "eslint-loader"]
                },
                {
                    test: /\.(css|scss)$/,
                    use: [
                        {
                            loader: "file-loader",
                            options: {
                                name: "css/[name].css"
                            }
                        },
                        "extract-loader",
                        {
                            loader: "css-loader",
                            options: {
                                url: false
                            }
                        },
                        "sass-loader"
                    ]
                },
                {
                    test: /\.(png|jpg|gif)$/,
                    use: [
                        {
                            loader: "url-loader",
                            options: {
                                limit: 5000
                            }
>>>>>>> eod commit
                        }
                    },
                    "extract-loader",
                    {
                        loader: "css-loader",
                        options: {
                            url: false
                        }
                    },
                    "sass-loader"
                ]
            },
            {
                test: /\.(png|jpg|gif)$/,
                use: [{
                    loader: "url-loader",
                    options: {
                        limit: 5000
                    }
                }]
            }
        ]
    }
}];
