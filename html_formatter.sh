#!/bin/bash
for filename in site/templates/*__.html; do
    cat $filename | sed s/_\(_/{{/ | sed s/_\)_/}}/ > site/templates/$(basename $filename __.html).html
done

