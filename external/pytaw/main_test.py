import pytaw

yt = pytaw.YouTube(key='AIzaSyBabzE4Bup77WexdLMa9rN9z-wJidEfNX8')
c = yt.channel('UCmmPgObSUPw1HL2lq6H4ffA')

uploads_playlist = c.uploads_playlist
print(repr(uploads_playlist))

uploads_list = list(uploads_playlist.items)
for item in uploads_list:
    print(item.position, '...', repr(item), ' .... ', repr(item.video))
    print(item.thumbnails)
    break
