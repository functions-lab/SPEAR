#!/bin/bash
find . -type f -name "*.py" -exec autopep8 --max-line-length=80 -i {} \;
