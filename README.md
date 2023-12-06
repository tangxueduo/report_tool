
# Downoloads
    pip install report-tool

# Development

    ## poetry 初始化
        1、　poetry init
        2、　poetry add package.
            # More examples，refer to: https://python-poetry.org/docs
            # Allow >=2.0.5, <3.0.0 versions
            poetry add pendulum@^2.0.5

            # Allow >=2.0.5, <2.1.0 versions
            poetry add pendulum@~2.0.5

            # Allow >=2.0.5 versions, without upper bound
            poetry add "pendulum>=2.0.5"

            # Allow only 2.0.5 version
            poetry add pendulum==2.0.5
        3、 poetry install 
        4、 激活虚拟环境　poetry shell 

    ## advices about git

    ## test wrap report_tool
    cur dir path: 
        pip install .
        python -c "import report_tool"
    ## git push to repos ("")

# Other
    








