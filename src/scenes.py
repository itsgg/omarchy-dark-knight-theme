"""Flat, resolution-independent Gotham architecture."""


def rect(x, y, w, h, fill):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"/>'


def tower(x, w, h, kind, fill, index, detail=True):
    body = rect(x, -h, w, h, fill)
    shade = '#111D25' if fill == '#172630' else '#101A22'
    if kind == 'deco':
        for inset, rise in ((.1, 18), (.22, 38), (.34, 58)):
            body += rect(x+w*inset, -h-rise, w*(1-2*inset), rise, fill)
        body += rect(x+w*.48, -h-93, w*.04, 40, fill)
        body += rect(x+w*.13, -h+20, w*.035, h-20, shade)
        body += rect(x+w*.82, -h+20, w*.035, h-20, shade)
    elif kind == 'gothic':
        body += (f'<path d="M{x:g} {-h:g}L{x+w*.12:g} {-h-35:g}'
                 f'L{x+w*.23:g} {-h:g}H{x+w*.77:g}L{x+w*.88:g} {-h-35:g}'
                 f'L{x+w:g} {-h:g}ZM{x+w*.26:g} {-h:g}'
                 f'L{x+w*.5:g} {-h-112:g}L{x+w*.74:g} {-h:g}Z" fill="{fill}"/>')
        body += rect(x+w*.48, -h-143, w*.04, 40, fill)
        for at in (.13, .82):
            body += rect(x+w*at, -h+12, w*.045, h-12, shade)
        body += rect(x-5, -h+85, w+10, 5, fill)
    elif kind == 'roof':
        body += rect(x-4, -h-6, w+8, 6, fill)
        body += rect(x+w*.15, -h-22, w*.32, 16, fill)
        if index % 2:
            # A water tank, drawn as broad shapes rather than tiny fittings.
            tx = x+w*.64
            body += (f'<path d="M{tx:g} {-h-35:g}L{tx+13:g} {-h-47:g}'
                     f'L{tx+26:g} {-h-35:g}V{-h-10:g}H{tx:g}Z" fill="{fill}"/>')
            body += rect(tx+3, -h-12, 3, 12, fill)
            body += rect(tx+20, -h-12, 3, 12, fill)
    if detail:
        body += rect(x+w*.85, -h+8, w*.15, h-8, shade)
        # Occasional broad occupied floors. Most buildings remain unlit.
        if index % 3 == 1:
            for floor in range(2 if h > 240 else 1):
                body += rect(x+w*.22, -h+48+floor*83, w*.39, 5, '#314550')
        body += rect(x+w*.08, -h+15, w*.73, 3, '#20323E')
    return body


def city(width, bottom, vertical=1, distant=False):
    layers = [
        ('#111D25', [(0,145,170,'roof'), (145,100,250,'deco'),
                     (245,155,200,'roof'), (430,120,310,'gothic'),
                     (550,130,210,'roof'), (710,95,290,'deco'),
                     (805,160,185,'roof'), (990,110,300,'gothic'),
                     (1100,155,195,'roof'), (1280,115,255,'deco'),
                     (1430,150,190,'roof'), (1610,100,280,'gothic'),
                     (1710,125,220,'roof'), (1835,85,175,'roof')]),
        ('#172630', [(0,125,165,'roof'), (155,135,265,'gothic'),
                     (320,145,215,'roof'), (490,115,365,'deco'),
                     (635,145,180,'roof'), (805,125,290,'deco'),
                     (960,120,185,'roof'), (1110,125,330,'gothic'),
                     (1270,170,190,'roof'), (1475,135,285,'deco'),
                     (1650,115,170,'roof'), (1795,125,240,'gothic')]),
        ('#0D171E', [(0,200,95,'roof'), (240,170,145,'roof'),
                     (445,210,110,'roof'), (700,145,175,'roof'),
                     (885,200,95,'roof'), (1125,180,135,'roof'),
                     (1340,190,100,'roof'), (1570,150,155,'roof'),
                     (1760,160,110,'roof')]),
    ]
    body = ''
    for layer_index, (fill, buildings) in enumerate(layers):
        body += rect(0, -25, 1920, 25, fill)
        for i, (x,w,h,kind) in enumerate(buildings):
            body += tower(x,w,h,kind,fill,i,detail=layer_index==1 and not distant)
    return (f'<g transform="translate(0 {bottom:g}) scale({width/1920:g} '
            f'{width/1920*vertical:g})">{body}</g>')
