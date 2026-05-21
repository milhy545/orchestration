#!/bin/bash
git stash
for pr in 142 141 140 126 124 121 117 110 99 84; do
    echo "Processing PR $pr"
    gh pr checkout $pr
    if git rebase master; then
        echo "Rebase successful, force pushing..."
        git push -f origin HEAD
        git checkout master
        git pull origin master
        gh pr merge $pr --squash --admin --delete-branch
        git pull origin master
    else
        echo "Rebase failed for $pr, aborting rebase"
        git rebase --abort
        git checkout master
    fi
done
