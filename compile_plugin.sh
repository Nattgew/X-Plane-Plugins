#!/bin/bash
gcc -fPIC -DLIN=1 -shared -rdynamic -nodefaultlibs -undefined_warning $1 -o ${1%.*}.xpl
gcc -m32 -fPIC -DLIN=1 -shared -rdynamic -nodefaultlibs -undefined_warning $1 -o ${1%.*}32.xpl
