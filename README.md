rss-python
==========
```
python downloader.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>
```
if you ommit --output it will create folder name 'download' on current path
```    
python downloader.py --feed=<RSS-Feed-URL>
```
downloader-thread.py downloads 5 files simultaneously using 5 threads. The number of threads can be increased or decreased. First the Queue is instanced. Then it is fulled with 5 threads with ThreadUrl object. Then instance of Downloader with urls from RSS feed. Then threads start downloading the files.  
```   
downloader-thread.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>
```
