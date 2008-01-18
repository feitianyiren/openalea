#!

LOCPATH=$(pwd)
rm -Rf dist
mkdir dist

for DIR in core visualea catalog deploy deploygui spatial stand stat plotools image
do
cd $DIR &&
rm -Rf build &&
rm -Rf dist &&
python setup.py bdist_egg -d ../dist sdist -d ../dist --format=gztar 
cd $LOCPATH
echo $LOCPATH
done
