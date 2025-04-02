echo "CurrentIP: `curl ipecho.net/plain`"
git fetch
git stash
git rebase origin/main
git stash pop

