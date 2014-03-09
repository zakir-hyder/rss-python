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
downloader-multiple-thread.py sends a request using HTTPConnection to each url to check if the file can be downloaded using range header. The program checks for 206 header response. If partial download possible the app create two threads - each thread downloads half of the file. Thread locks its self when it starts to write the file on HDD not while downloading. If partial download is not possible the url is added to queue like downloader-queue-thread.py
``` 
python downloader-multiple-thread.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>
```