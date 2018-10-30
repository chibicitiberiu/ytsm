# PYTAW: Python YouTube API Wrapper

###Note
This library is copied from [https://github.com/chibicitiberiu/pytaw/tree/improvements](https://github.com/chibicitiberiu/pytaw/tree/improvements).


```python
>>> from pytaw import YouTube
>>> youtube = YouTube(key='your_api_key')
>>> video = youtube.video('4vuW6tQ0218')
>>> video.title
'Monty Python - Dead Parrot'
>>> video.published_at
datetime.datetime(2007, 2, 14, 13, 55, 51, tzinfo=tzutc())
>>> channel = video.channel
>>> channel.title
'Chadner'
>>> search = youtube.search(q='monty python')
>>> search[0]
<Channel UCGm3CO6LPcN-Y7HIuyE0Rew "Monty Python">
>>> for r in search[:5]:
...     print(r)
...     
Monty Python
Chemist Sketch - Monty Python's Flying Circus
A Selection of Sketches from "Monty Python's Flying Circus" - #4
Monty Python - Dead Parrot
Monty Python And the holy grail
```