#!/bin/bash
set -e

#cd backup-agent-web
#npm install
#ng build --prod
#cd ..

cd fm
npm install
gulp build || node node_modules/gulp/bin/gulp.js build
cd ..

cp fm/index.html api/browse

rm -rf api/browse/dist
cp -r fm/dist api/browse/dist

rm -rf api/browse/node_modules
mkdir -p api/browse/node_modules/jquery/dist && cp fm/node_modules/jquery/dist/jquery.min.js api/browse/node_modules/jquery/dist/jquery.min.js
mkdir -p api/browse/node_modules/angular && cp fm/node_modules/angular/angular.min.js api/browse/node_modules/angular/angular.min.js
mkdir -p api/browse/node_modules/angular-translate/dist && cp fm/node_modules/angular-translate/dist/angular-translate.min.js api/browse/node_modules/angular-translate/dist/angular-translate.min.js
mkdir -p api/browse/node_modules/ng-file-upload/dist && cp fm/node_modules/ng-file-upload/dist/ng-file-upload.min.js api/browse/node_modules/ng-file-upload/dist/ng-file-upload.min.js
mkdir -p api/browse/node_modules/bootstrap/dist/js && cp fm/node_modules/bootstrap/dist/js/bootstrap.min.js api/browse/node_modules/bootstrap/dist/js/bootstrap.min.js
mkdir -p api/browse/node_modules/bootswatch/paper && cp fm/node_modules/bootswatch/paper/bootstrap.min.css api/browse/node_modules/bootswatch/paper/bootstrap.min.css
mkdir -p api/browse/node_modules/bootswatch/fonts && cp fm/node_modules/bootswatch/fonts/* api/browse/node_modules/bootswatch/fonts

# increment the build number
cat api/buildnumber.txt | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{if(length($NF+1)>length($NF))$(NF-1)++; $NF=sprintf("%0*d", length($NF), ($NF+1)%(10^length($NF))); print}' > tmp && sleep 1 &&  mv tmp api/buildnumber.txt

