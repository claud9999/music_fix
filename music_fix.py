#!/usr/bin/env python3

import applescript, titlecase, argparse, sys, pdb

parser = argparse.ArgumentParser()
parser.add_argument('--disccnt', action='store_true')
parser.add_argument('--trackcnt', action='store_true')
parser.add_argument('--remove_album_artist', action='store_true')
parser.add_argument('--cap_artist', action='store_true')
parser.add_argument('--cap_album', action='store_true')
parser.add_argument('--cap_name', action='store_true')
parser.add_argument('--album_genre', action='store_true')
parser.add_argument('--artist_parens', action='store_true')
args = parser.parse_args()

tracks = []

class track_class:
    def __init__(self, id, album, album_artist, artist, name, disc_num, disc_cnt, track_num, track_cnt, genre):
        self.id = id
        self.fields = {
            'album': album,
            'album artist': album_artist,
            'artist': artist,
            'name': name,
            'disc number': disc_num,
            'disc count': disc_cnt,
            'track number': track_num,
            'track count': track_cnt,
            'genre': genre
        }
        self.dirty = {}

    def __repr__(self):
        return "<track %r>" % (self.fields)

    def set(self, field, value):
        if self.fields[field] == value: return
        self.dirty[field] = True
        self.fields[field] = value

    def updates(self):
        r = ''
        for field in self.dirty.keys():
            v = self.fields[field]
            if type(v) == int: v = '%d' % v
            else: v = '"%s"' % v
            if r: r = '%s\nset %s of t to %s' % (r, field, v)
            else: r = 'set %s of t to %s' % (field, v)
        return r

sel = applescript.tell.app('Music', 'return selection').out.split(',')
for t in sel:
    r = applescript.tell.app('Music', '''
    set t to %s
    set track_num to track number of t as text
    set track_cnt to track count of t as  text
    set disc_num to disc number of t as  text
    set disc_cnt to disc count of t as  text
    set track_name to name of t
    set track_artist to artist of t
    set album_artist to album artist of t
    set track_album to album of t
    set track_genre to genre of t
    return track_num & "/" & track_cnt & "\\n" & disc_num & "/" & disc_cnt & "\\n" & album_artist & "\\n" & track_artist & "\\n" & track_album & "\\n" & track_name & "\\n" & track_genre & "\\nend"
    ''' % (t,))
    if r.err:
        print(r.err)
        continue
    (track, disc, album_artist, artist, album, name, genre, end) = r.out.split('\n')
    (track_num, track_cnt) = track.split('/')
    track_num = int(track_num)
    track_cnt = int(track_cnt)
    (disc_num, disc_cnt) = disc.split('/')
    disc_num = int(disc_num)
    disc_cnt = int(disc_cnt)
    tracks.append(track_class(t, album, album_artist, artist, name, disc_num, disc_cnt, track_num, track_cnt, genre))

if args.trackcnt:
    last_track = {}
    for track in tracks:
        a = track.fields['album']
        n = track.fields['track number']
        if a not in last_track or last_track[a] < n:
            last_track[a] = n
    for track in tracks:
        track.set('track count', last_track[track.fields['album']])

if args.disccnt:
    last_disc = {}
    for track in tracks:
        a = track.fields['album']
        n = track.fields['disc number']
        if not n:
            n = 1
            track.set('disc number', 1)
        if a not in last_disc or last_disc[a] < n: last_disc[a] = n
    for track in tracks:
        track.set('disc count', last_disc[track.fields['album']])

if args.remove_album_artist:
    for track in tracks:
        if track.fields['album artist']: track.set('album artist', '')

if args.artist_parens:
    for track in tracks:
        if '(' in track.fields['artist']:
            track.set('artist', track.fields['artist'].split(' (')[0])

if args.cap_artist:
    for track in tracks:
        a = track.fields['artist']
        a_cap = titlecase.titlecase(a)
        if a != a_cap: track.set('artist', a_cap)

if args.album_genre:
    for track in tracks:
        a = track.fields['album']
        if '(' in a:
            (album, genre) = a.split(' (')
            genre = genre.split(')')[0]
            track.set('album', album)
            track.set('genre', genre)

if args.cap_album:
    for track in tracks:
        a = track.fields['album']
        a_cap = titlecase.titlecase(a)
        if a != a_cap: track.set('album', a_cap)

if args.cap_name:
    for track in tracks:
        a = track.fields['name']
        a_cap = titlecase.titlecase(a)
        if a != a_cap: track.set('name', a_cap)

m = ''
for track in tracks:
    u = track.updates()
    if not u: continue
    m = '''%s
        set t to %s
        %s
        ''' % (m, track.id, track.updates())

r = applescript.tell.app('Music', m)
if r.err: print('ERR: %r' % r.err)
