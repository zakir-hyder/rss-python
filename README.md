rss-python
==========
```
python downloader.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>
```
if you ommit --output it will create folder name 'download' on current path
```    
python downloader.py --feed=<RSS-Feed-URL>
```
downloader-queue-thread.py downloads all the files in xml simultaneously using pool of thread threads. The number of threads can be increased or decreased if wanted. The daemon threads calls ThreadUrl function which pop Downloader object from queue and calls download function to download the file. After finishing the downloading the file thread pop another Downloader object and so on. As the threads are daemon they will be killed as program quits  
```   
python downloader-queue-thread.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>
```
downloader-thread.py downloads all the files in xml simultaneously. using equal number of threads. The number of threads is equal to links in xml.  
```   
python downloader-thread.py--feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>
```