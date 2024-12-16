if [ $# -eq 0 ]
then
    echo 'commit message is needed!'
    exit 1
else
    # date +'%Y-%m-%d %H:%M:%S' > version.txt
    git add *
    git commit -a -m "$1"
    git status
    git push
fi


