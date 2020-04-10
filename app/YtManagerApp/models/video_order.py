VIDEO_ORDER_CHOICES = [
    ('newest', 'Newest'),
    ('oldest', 'Oldest'),
    ('playlist', 'Playlist order'),
    ('playlist_reverse', 'Reverse playlist order'),
    ('popularity', 'Popularity'),
    ('rating', 'Top rated'),
]

VIDEO_ORDER_MAPPING = {
    'newest': '-publish_date',
    'oldest': 'publish_date',
    'playlist': 'playlist_index',
    'playlist_reverse': '-playlist_index',
    'popularity': '-views',
    'rating': '-rating'
}
