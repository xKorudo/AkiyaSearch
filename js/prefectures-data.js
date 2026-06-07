// Shared prefecture data for prefectures.html (overview) and prefecture.html (detail).
// slug = English name lowercased with spaces as hyphens.
// `long` is an array of paragraphs (rendered as separate <p> on the detail page).
window.PREFECTURES = [
  { en:'Hokkaido', kanji:'北海道', region:'Hokkaidō',
    short:'Japan’s vast northern island — nature, powder snow, dairy and seafood.',
    highlights:['Powder-snow skiing (Niseko, Furano)','Dairy, crab, salmon & sea urchin','Sapporo: beer, miso ramen, Snow Festival','National parks, lavender, wide-open space'],
    long:[
      'Hokkaidō is Japan’s northernmost and largest prefecture, accounting for over a fifth of the country’s land area but only about 4% of its population. Settled in earnest only from the late 19th century, it has a frontier feel unlike anywhere else in Japan: arrow-straight roads, huge farms, and a grid-planned capital, Sapporo. It is also the homeland of the indigenous Ainu, whose language and culture survive in place names and museums such as Upopoy near Lake Shiraoi.',
      'The island is famous worldwide for snow. Resorts like Niseko, Furano and Rusutsu receive extraordinarily light, dry powder, drawing skiers from across Asia and Australia. Summers, by contrast, are mild and dry — a relief from Honshū’s humidity — making it peak season for hiking in national parks such as Daisetsuzan and Shiretoko (a UNESCO natural site), and for the lavender fields of Furano.',
      'Hokkaidō is Japan’s breadbasket and dairy: it leads the nation in milk, butter, potatoes, corn, wheat and much more, while its cold seas yield crab, salmon, scallops and sea urchin. Sapporo gives its name to beer and to rich miso ramen, and hosts the giant February Snow Festival. With low land prices, abundant space and many vacant homes, it is a favourite for buyers seeking nature and room to breathe — though heating and snow-clearing are real winter considerations.'
    ] },

  { en:'Aomori', kanji:'青森', region:'Tōhoku',
    short:'Apple country at Honshū’s northern tip, home of the Nebuta festival.',
    highlights:['Most of Japan’s apples','Nebuta Matsuri (giant lit floats)','Hakkōda mountains, Lake Towada','Jōmon Sannai-Maruyama site (UNESCO)'],
    long:[
      'Aomori sits at the very top of Honshū, separated from Hokkaidō by the Tsugaru Strait and split by two great peninsulas into the Sea of Japan and Pacific sides. It is one of Japan’s snowiest inhabited regions — the city of Aomori is among the snowiest provincial capitals on Earth — and winters shape daily life and architecture here.',
      'The prefecture grows the majority of Japan’s apples, and orchards blanket the Tsugaru plain around Hirosaki, a castle town famous for its spring cherry blossoms. In early August the Nebuta Matsuri fills Aomori City with enormous illuminated paper floats and chanting dancers, one of the country’s most spectacular festivals. Folk traditions run deep, from Tsugaru-jamisen shamisen music to the distinctive local dialect.',
      'Nature and antiquity are major draws: the Hakkōda mountains offer hiking and famous hot springs (and deep backcountry snow), while crater-lake Towada and the Oirase mountain stream are classic scenery. The Sannai-Maruyama site near Aomori City preserves a large 5,500-year-old Jōmon settlement and is part of a UNESCO World Heritage listing. Ōma, at the tip of the Shimokita Peninsula, is renowned for prize bluefin tuna.'
    ] },

  { en:'Iwate', kanji:'岩手', region:'Tōhoku',
    short:'Huge, rural prefecture of temples, rugged coast and folklore.',
    highlights:['Hiraizumi temples (UNESCO)','Sanriku coast & seafood','Tōno folklore','Wanko-soba & reimen noodles'],
    long:[
      'Iwate is the largest prefecture on Honshū and one of the most sparsely populated, a land of mountains, forests and a long, indented Pacific coastline. Its low density and abundant nature have made it a byword for rural Japan, and it offers some of the country’s most affordable rural property.',
      'Its cultural jewel is Hiraizumi, capital of the northern Fujiwara clan in the 12th century, whose Chūson-ji temple — with its gold-leafed Konjikidō hall — and surrounding “Pure Land” gardens form a UNESCO World Heritage Site. The town of Tōno is celebrated as the cradle of Japanese folklore, immortalised in the “Legends of Tōno,” with tales of kappa water-sprites and zashiki-warashi house spirits.',
      'The Sanriku coast, badly hit by the 2011 tsunami and since rebuilt, is prized for dramatic cliffs (Jōdogahama) and superb seafood, and is now linked by a scenic railway. Morioka, the lively capital, is known for its “three great noodles” — wanko-soba served in endless tiny bowls, chewy cold reimen, and jajamen — and was spotlighted internationally as a top travel destination. Winters are cold and snowy inland.'
    ] },

  { en:'Miyagi', kanji:'宮城', region:'Tōhoku',
    short:'Tōhoku’s hub around Sendai, beef tongue and the bay of Matsushima.',
    highlights:['Sendai, the “City of Trees”','Gyūtan (grilled beef tongue)','Matsushima bay (top-3 view)','Date Masamune history'],
    long:[
      'Miyagi is the economic and cultural heart of the Tōhoku region, centred on Sendai — the north’s largest city and a green, leafy place nicknamed the “City of Trees.” Founded around 1600 by the one-eyed warlord Date Masamune, Sendai blends a relaxed regional-capital feel with universities, shopping arcades and an easy bullet-train hop to Tokyo.',
      'The prefecture’s signature dish is gyūtan, thick-sliced grilled beef tongue, a postwar Sendai invention now eaten nationwide. Just up the coast, Matsushima Bay — dotted with some 260 pine-clad islets — is traditionally counted among the “Three Views of Japan,” best appreciated by boat or from hilltop temples like Zuiganji. The Tanabata star festival each August is one of Japan’s most famous.',
      'Miyagi faces the Pacific and is a major fishing and rice-growing region; oysters, sea squirt and Sasanishiki/Hitomebore rice are local staples. The coast was the epicentre region of the 2011 earthquake and tsunami and has since been extensively rebuilt, with memorial sites and revitalised port towns. Inland lie ski slopes, the Naruko hot-spring valley and the Zaō mountains shared with Yamagata.'
    ] },

  { en:'Akita', kanji:'秋田', region:'Tōhoku',
    short:'Rural snow country of Akita dogs, rice, sake and Namahage.',
    highlights:['Akita dog breed','Top-grade rice & sake','Kantō lantern festival','Namahage tradition; Lake Tazawa'],
    long:[
      'Akita, on the Sea of Japan side of northern Honshū, is deep snow country and one of Japan’s most rapidly aging and depopulating prefectures — which also means plentiful, inexpensive akiya and a strong push to welcome newcomers. Its fertile plains and clean water make it a premier producer of rice and, from that rice, some of Japan’s most respected sake.',
      'The prefecture lends its name to the Akita-inu, the large, loyal native dog breed made famous worldwide by the story of Hachikō. Local culture is rich and distinctive: the summer Kantō Matsuri sees performers balance long bamboo poles strung with dozens of paper lanterns on their hands, hips and foreheads, while around the New Year the Namahage of the Oga Peninsula — costumed “ogres” — visit homes to scold idlers and bless families (a UNESCO-listed tradition).',
      'Scenery is a highlight too: Lake Tazawa is Japan’s deepest and a brilliant cobalt blue, the samurai town of Kakunodate preserves weeping-cherry-lined streets and old residences, and Nyūtō Onsen is a beloved cluster of rustic hot springs. Winters are long and heavy with snow, so insulation and snow management matter for any home here.'
    ] },

  { en:'Yamagata', kanji:'山形', region:'Tōhoku',
    short:'Mountainous fruit-and-pilgrimage prefecture; cherries and onsen.',
    highlights:['Japan’s top cherries','Mt. Zaō “snow monsters”','Dewa Sanzan sacred peaks','Ginzan Onsen, Yamadera temple'],
    long:[
      'Yamagata lies on the Sea of Japan side of Tōhoku, almost entirely ringed by mountains and drained by the Mogami River. The basins between the ranges have a hot, humid summer ideal for fruit: Yamagata is Japan’s leading producer of cherries (the prized Satō Nishiki variety) and grows excellent pears, grapes and the “La France” pear.',
      'Spirituality is woven into its mountains. The Dewa Sanzan — Mounts Haguro, Gassan and Yudono — are sacred to the ascetic Shugendō tradition, with a famous five-storied pagoda and a long cedar-lined stone staircase on Haguro. The cliffside temple complex of Yamadera (Risshaku-ji), where the poet Bashō wrote a celebrated haiku, rewards a steep climb with sweeping valley views.',
      'In winter, Mount Zaō is famous for its “snow monsters” (jūhyō) — fir trees encased in wind-driven frost — and for skiing and hot springs. The silver-mining spa town of Ginzan Onsen, with its gas-lit wooden ryokan along a river, is one of Japan’s most atmospheric onsen villages. Quiet, scenic and traditional, Yamagata offers abundant rural homes amid orchards and hot springs.'
    ] },

  { en:'Fukushima', kanji:'福島', region:'Tōhoku',
    short:'Large prefecture of samurai history, peaches and post towns.',
    highlights:['Aizu samurai history & Tsuruga Castle','Ōuchi-juku thatched post town','Peaches, rice & sake','Mountains, lakes & onsen'],
    long:[
      'Fukushima is Japan’s third-largest prefecture and divides naturally into three: the Pacific “Hamadōri” coast, the central “Nakadōri” corridor of cities and orchards, and the mountainous, snowy “Aizu” west. This variety gives it everything from beaches to ski resorts within a couple of hours’ drive.',
      'Aizu is steeped in samurai history. Aizu-Wakamatsu’s reconstructed Tsuruga Castle and the tragic tale of the teenage Byakkotai warriors are central to the region’s identity, and nearby the Edo-era post town of Ōuchi-juku preserves a street of thatched-roof houses that is magical under snow. The Nakadōri belt is famous for peaches and other fruit, plus rice and award-winning sake.',
      'The 2011 earthquake and the Fukushima Daiichi nuclear accident affected a defined coastal zone; the great majority of the prefecture is open, safe and actively revitalising, with strong support for newcomers and creative reuse of empty homes. Natural highlights include Lake Inawashiro beneath Mount Bandai, the Goshikinuma “five-coloured” ponds, and numerous hot springs such as Iizaka and Tsuchiyu.'
    ] },

  { en:'Ibaraki', kanji:'茨城', region:'Kantō',
    short:'Farmland-and-seaside neighbour of Tokyo; flowers and nattō.',
    highlights:['Hitachi Seaside Park flowers','Home of nattō','Mt. Tsukuba; Tsukuba science city','Kairaku-en plum garden'],
    long:[
      'Ibaraki sits just northeast of Tokyo on the Pacific, a flat, fertile and underrated prefecture that combines serious farming with easy access to the capital. It is one of Japan’s top agricultural producers, and is most famous nationally as the home of nattō — sticky fermented soybeans, a love-it-or-hate-it breakfast staple closely tied to the city of Mito.',
      'Its best-known sight is Hitachi Seaside Park, whose hillsides turn sky-blue with millions of nemophila flowers in spring and fiery red with kochia in autumn — one of Japan’s most photographed landscapes. Mito’s Kairaku-en, created by a feudal lord, is counted among the country’s three great gardens and is celebrated for its plum blossoms.',
      'Mount Tsukuba, an easily climbed twin-peaked mountain, rises from the plain and is paired with Tsukuba Science City, a planned hub of national research institutes and universities. The coast offers surfing and the towering bronze Ushiku Daibutsu Buddha stands among the tallest statues in the world. With Tokyo within commuting reach yet land far cheaper, Ibaraki appeals to those wanting space near the capital.'
    ] },

  { en:'Tochigi', kanji:'栃木', region:'Kantō',
    short:'Inland Kantō prefecture famous for Nikkō’s shrines and strawberries.',
    highlights:['Nikkō Tōshō-gū (UNESCO)','Japan’s #1 strawberries','Ashikaga wisteria','Utsunomiya gyōza'],
    long:[
      'Tochigi is a landlocked prefecture north of Tokyo, rising from the Kantō plain into the mountains of Nikkō. Its headline attraction is the Nikkō shrine-and-temple complex, a UNESCO World Heritage Site centred on the lavishly carved Tōshō-gū, the mausoleum of Tokugawa Ieyasu, founder of the shogunate — home of the famous “see/hear/speak no evil” monkeys and a sleeping-cat carving.',
      'Above Nikkō, the Oku-Nikkō highlands offer Lake Chūzenji, the thundering Kegon Falls and the Senjōgahara marshland, brilliant in autumn colour and cool in summer. The historic Kanuma and Mashiko areas are known for crafts, Mashiko in particular for its rustic pottery.',
      'Down on the plain, Tochigi is Japan’s number-one strawberry producer (the Tochiotome variety), and Ashikaga Flower Park draws crowds for its vast, illuminated wisteria trellises each spring. The capital, Utsunomiya, is nationally famous for gyōza dumplings. Well connected by bullet train yet largely rural, Tochigi balances day-trip convenience with affordable countryside.'
    ] },

  { en:'Gunma', kanji:'群馬', region:'Kantō',
    short:'Landlocked mountain prefecture of famous hot springs.',
    highlights:['Kusatsu, Ikaho & Minakami onsen','Tomioka Silk Mill (UNESCO)','Hiking & skiing','Daruma dolls, konnyaku'],
    long:[
      'Gunma is a landlocked, mountainous prefecture northwest of Tokyo, long associated with hot springs and mountain scenery. Its onsen resorts are among Japan’s most celebrated: Kusatsu, with its steaming central “yubatake” hot-water field and famously potent acidic waters; the hillside spa of Ikaho with its stone stairway; and Minakami, a hub for rafting, hiking and skiing.',
      'The prefecture played a pivotal role in Japan’s modernisation through silk. The Tomioka Silk Mill, a model government factory opened in 1872, is a UNESCO World Heritage Site that helped turn Japan into a silk-exporting power. Gunma is also the home of the daruma good-luck doll (Takasaki) and a leading grower of konnyaku and cabbage on the cool Tsumagoi highlands.',
      'Outdoors, Gunma offers serious mountains — Tanigawa-dake for hikers and climbers, Mount Haruna and Mount Akagi’s crater lake, and winter resorts that are popular weekend escapes. With Tokyo reachable by bullet train but housing far cheaper, its valleys and onsen towns hold many vacant homes well suited to rural or second-home life.'
    ] },

  { en:'Saitama', kanji:'埼玉', region:'Kantō',
    short:'Tokyo’s northern suburbs with “Little Edo” Kawagoe.',
    highlights:['Kawagoe “Little Edo”','Chichibu mountains & festivals','Easy Tokyo commute','Sembei crackers, Sayama tea'],
    long:[
      'Saitama wraps around the northern side of Tokyo and is one of Japan’s most populous prefectures, functioning largely as a commuter belt for the capital. That makes it practical rather than glamorous — but it offers far more affordable housing within easy train reach of central Tokyo, and pockets of real charm.',
      'Its star attraction is Kawagoe, nicknamed “Little Edo” for its preserved street of clay-walled kurazukuri merchant warehouses and the landmark “Bell of Time” tower, plus a lane of traditional sweet shops. It evokes the look of old Tokyo that the capital itself has largely lost.',
      'In the west, the Chichibu mountains provide hiking, the Hitsujiyama Park shibazakura (pink moss) fields, dramatic night festivals and river gorges — a quick nature fix from the city. Saitama is also known for Sayama green tea, sembei rice crackers and, increasingly, anime tourism. For buyers it is the place to balance countryside or town life with a genuinely commutable link to Tokyo.'
    ] },

  { en:'Chiba', kanji:'千葉', region:'Kantō',
    short:'Tokyo Bay prefecture — Narita Airport, Disney, surf and peanuts.',
    highlights:['Narita International Airport','Tokyo Disney Resort','Bōsō surf beaches & Nokogiriyama','Peanuts; soy-sauce brewing'],
    long:[
      'Chiba occupies the peninsula east of Tokyo, wrapping around the bay and out to the Pacific. It is the gateway to Japan for most international visitors, since Narita International Airport sits here, and — despite the name — the Tokyo Disney Resort is actually in Urayasu, Chiba, right on the bay.',
      'The Bōsō Peninsula gives the prefecture a coastal, outdoors character very different from inland Kantō: long surf beaches around Kujūkuri and Ichinomiya (a venue for Olympic surfing), fishing ports, flower fields that bloom early in the mild climate, and the clifftop temple and “hell-peek” viewpoint of Nokogiriyama. Cape Inubō catches Japan’s earliest mainland sunrise.',
      'Agriculturally Chiba is a powerhouse close to the capital — it is Japan’s top producer of peanuts and a major source of vegetables — and the towns of Noda and Chōshi are historic centres of soy-sauce brewing (Kikkoman’s home). Narita’s own old town, anchored by the grand Naritasan temple, makes a rewarding stop. Coastal southern Chiba, milder and increasingly popular for surf and remote work, has a growing akiya scene.'
    ] },

  { en:'Tokyo', kanji:'東京', region:'Kantō',
    short:'Japan’s capital — culture, business, food and trends.',
    highlights:['World city: Shinjuku, Shibuya','Most Michelin stars on Earth','Imperial gardens & historic Asakusa','Western mountains & Pacific islands'],
    long:[
      'Tokyo is Japan’s capital and the centre of the world’s largest metropolitan area, home to well over 30 million people in its wider region. It is the engine of the nation’s government, finance, media, fashion and pop culture — a place of staggering density and energy where neon districts like Shinjuku, Shibuya and Akihabara sit minutes from the quiet moats of the Imperial Palace.',
      'For all its modernity, Tokyo keeps deep layers of history: the great Sensō-ji temple in Asakusa, the Meiji Shrine’s forest, sumo in Ryōgoku, and beautiful landscape gardens such as Rikugien. Its food scene is unrivalled — Tokyo holds more Michelin stars than any other city, alongside endless ramen counters, izakaya and the Toyosu fish market.',
      'The prefecture is far larger than the 23 central wards. West of the city, the Tama region rises into real mountains around Okutama and Mount Takao, and Tokyo even administers remote Pacific islands — the Izu and Ogasawara (Bonin) chains, the latter a UNESCO natural World Heritage Site. Property in central Tokyo is among Japan’s most expensive, but the western suburbs and outlying towns are far more attainable.'
    ] },

  { en:'Kanagawa', kanji:'神奈川', region:'Kantō',
    short:'Just south of Tokyo — Yokohama, Kamakura and Hakone.',
    highlights:['Yokohama port & Chinatown','Kamakura Great Buddha','Hakone onsen & Mt. Fuji views','Enoshima beaches & surf'],
    long:[
      'Kanagawa lies immediately south of Tokyo and is one of Japan’s most populous and prosperous prefectures, yet it packs in remarkable variety within a small area. Yokohama, its capital, is Japan’s second-largest city — a cosmopolitan port that opened to the world in 1859, with the country’s largest Chinatown, a stylish bayfront (Minato Mirai) and a long maritime history.',
      'History and the sea define its south. Kamakura, Japan’s capital in the 12th–14th centuries, is a temple-rich town beside the beach, famous for its giant open-air bronze Great Buddha and the hydrangeas of Hase-dera, while neighbouring Enoshima island and the Shōnan coast are beloved for surfing and a laid-back beach culture within easy reach of Tokyo.',
      'In the west, Hakone is one of Japan’s premier hot-spring resorts, with open-air baths, art museums, the volcanic Ōwakudani valley and classic views of Mount Fuji across Lake Ashi. With excellent rail links throughout, Kanagawa offers everything from dense city living to seaside towns and mountain spa villages — though prices near Tokyo and the coast run high.'
    ] },

  { en:'Niigata', kanji:'新潟', region:'Chūbu',
    short:'Sea-of-Japan rice and sake country, deep in “snow country”.',
    highlights:['Koshihikari rice & sake','Heavy-snow ski resorts','Sado Island','Coastal seafood'],
    long:[
      'Niigata stretches along the Sea of Japan coast, a long prefecture of fertile plains backed by mountains. Its Echigo plain, watered by the Shinano (Japan’s longest river), produces the country’s most famous rice — premium Koshihikari — which in turn feeds a celebrated sake industry of around 90 breweries, more than almost anywhere in Japan.',
      'This is the original “snow country” of Kawabata’s Nobel-winning novel: moist Siberian winds dump enormous snowfall on the mountains, creating superb, easily reached ski resorts such as Echigo-Yuzawa and Myōkō, along with countless hot springs. The same water and snow underpin the rice and sake that define local life.',
      'Offshore, Sado Island is a world of its own — once a place of exile and a gold-mining boomtown, now known for folk traditions, the Kodō taiko drummers and conservation of the rare crested ibis (toki). Niigata City is a workmanlike regional capital with good seafood. Inexpensive rural homes are plentiful, with the trade-off of serious winter snow.'
    ] },

  { en:'Toyama', kanji:'富山', region:'Chūbu',
    short:'Alps-and-bay prefecture; snow walls, glass art and seafood.',
    highlights:['Tateyama Alpine Route snow walls','Firefly squid & white shrimp','Contemporary glass art','Gokayama gasshō villages (UNESCO)'],
    long:[
      'Toyama is cupped between the towering Northern Japan Alps and the deep waters of Toyama Bay, giving it one of the most dramatic landscapes in the country. Its signature experience is the Tateyama Kurobe Alpine Route, a chain of cable cars, buses and trolleys crossing the mountains past the vast Kurobe Dam and through a corridor where spring snow walls can rise nearly 20 metres on either side.',
      'The bay is famous for seafood found almost nowhere else: glowing firefly squid (hotaru-ika) that light up the spring shoreline, sweet raw white shrimp, and superb yellowtail. Toyama City has reinvented itself around contemporary glass art, with a striking glass museum and studios, building on a local pharmaceutical and bottle-making heritage.',
      'In the mountains, the thatched gasshō-zukuri farmhouses of Gokayama form part of a UNESCO World Heritage listing shared with Gifu’s Shirakawa-gō, but see far fewer crowds. Toyama is also one of Japan’s most car- and home-owning prefectures, with relatively spacious, affordable housing and reliable bullet-train access to Tokyo.'
    ] },

  { en:'Ishikawa', kanji:'石川', region:'Chūbu',
    short:'Cultured prefecture around Kanazawa — gardens, gold leaf, crafts.',
    highlights:['Kanazawa: Kenroku-en, geisha & samurai districts','Most of Japan’s gold leaf','Wajima lacquer, Kutani porcelain','Noto Peninsula coast'],
    long:[
      'Ishikawa, on the Sea of Japan coast, is one of Japan’s great strongholds of traditional culture, thanks to the wealth of the Maeda lords who ruled the Kaga domain. Their former castle town, Kanazawa, escaped wartime bombing and so preserves whole districts of old wooden architecture: the Higashi Chaya geisha quarter, the Nagamachi samurai residences, and Kenroku-en, ranked among the three most beautiful landscape gardens in Japan.',
      'That patronage created enduring crafts. Ishikawa produces virtually all of Japan’s gold leaf (used on temples and even sprinkled on local ice cream), as well as prized Wajima-nuri lacquerware, colourful Kutani porcelain and Kaga silk dyeing. Kanazawa balances this heritage with the bold 21st Century Museum of Contemporary Art.',
      'North of the city, the Noto Peninsula juts into the sea with rugged coastline, terraced rice fields running down to the water at Shiroyone Senmaida, morning markets and a slow rural pace; parts were struck by a major earthquake in early 2024 and are rebuilding. Kanazawa’s bullet-train link to Tokyo has boosted interest in the region.'
    ] },

  { en:'Fukui', kanji:'福井', region:'Chūbu',
    short:'Quiet prefecture of dinosaurs, Zen and sea cliffs.',
    highlights:['Dinosaur Museum & fossils','Eihei-ji Zen temple','Tōjinbō sea cliffs','Eyeglasses; Echizen crab'],
    long:[
      'Fukui is a quiet, often-overlooked prefecture on the Sea of Japan coast, regularly ranked among Japan’s best places to live for its low crime, strong schools and high rates of home and car ownership. It rewards visitors with an unusual mix of attractions for its size.',
      'It is Japan’s “dinosaur kingdom”: the country’s richest dinosaur fossil beds lie in Katsuyama, served by the excellent Fukui Prefectural Dinosaur Museum. The vast mountain temple of Eihei-ji, founded in 1244, is one of the two head temples of Sōtō Zen and a serene place where monks still train. On the coast, the basalt columns of the Tōjinbō cliffs drop sheer into the sea.',
      'Fukui is also an industrial specialist — the Sabae area makes the great majority of Japan’s eyeglass frames — and a source of luxury winter food in the form of Echizen snow crab. Echizen washi paper and lacquer add to its craft credentials. With a new bullet-train extension improving access, its affordable towns and countryside are drawing fresh attention.'
    ] },

  { en:'Yamanashi', kanji:'山梨', region:'Chūbu',
    short:'Mt. Fuji’s lakes, Japan’s wine country and fruit orchards.',
    highlights:['Fuji Five Lakes (Kawaguchiko)','Japan’s leading wine region','Peaches & grapes','Hot springs & Southern Alps hiking'],
    long:[
      'Yamanashi is a landlocked, mountain-ringed prefecture just west of Tokyo, best known for its front-row views of Mount Fuji. The Fuji Five Lakes district around Kawaguchiko is the classic place to photograph the peak mirrored in water or rising behind cherry blossoms and pagodas, and it is the main gateway for climbing Fuji in summer.',
      'The Kōfu basin enjoys long sunshine and big day-night temperature swings, perfect for fruit. Yamanashi is Japan’s top producer of peaches and grapes and the heart of its wine industry, centred on the native Kōshū grape around Katsunuma, where dozens of wineries offer tastings. Fruit-picking is a popular summer outing.',
      'The prefecture is also a hiker’s base, flanked by the Southern Japan Alps and the volcanic Yatsugatake range, with abundant hot springs (the historic Isawa Onsen among them). Close enough for a Tokyo day trip yet distinctly rural, Yamanashi has become a favourite for second homes and for people relocating to combine countryside life with proximity to the capital.'
    ] },

  { en:'Nagano', kanji:'長野', region:'Chūbu',
    short:'Alpine prefecture of ski resorts, snow monkeys and soba.',
    highlights:['Japanese Alps & 1998 Olympics','Jigokudani snow monkeys','Zenkō-ji & Matsumoto Castle','Soba, apples, wasabi'],
    long:[
      'Nagano is a large, high, landlocked prefecture often called the “roof of Japan,” enclosing much of the Japan Alps. It hosted the 1998 Winter Olympics, and its mountains deliver some of the country’s best skiing and snowboarding — Hakuba, Nozawa Onsen and Shiga Kōgen among many — plus world-class summer hiking around Kamikōchi and the Kiso Valley.',
      'It draws a famous mix of visitors to its wildlife and heritage. The snow monkeys of Jigokudani bathe in a steaming hot-spring pool, an internationally photographed sight; the ancient temple of Zenkō-ji anchors Nagano City; and Matsumoto guards one of Japan’s finest surviving original castles, its black keep nicknamed the “Crow Castle.” The old post towns of the Nakasendō, such as Tsumago and Narai, preserve Edo-era streetscapes.',
      'The cool highland climate suits soba (buckwheat) noodles, apples, grapes and Japan’s largest wasabi farm near Azumino. Long associated with healthy longevity, Nagano blends outdoor life, hot springs and history; its mountain villages and old towns hold many akiya, though winters are cold and snowy.'
    ] },

  { en:'Gifu', kanji:'岐阜', region:'Chūbu',
    short:'River-to-mountain prefecture; thatched villages and old towns.',
    highlights:['Shirakawa-gō gasshō houses (UNESCO)','Old-town Takayama','Gujō Hachiman dance','Cormorant fishing; Hida beef'],
    long:[
      'Gifu sits in the middle of Honshū, running from the flat, river-laced plains of the south up into the steep Hida mountains of the north. That northern Hida region is its scenic heart and the source of much of its fame.',
      'The mountain village of Shirakawa-gō, with its steep thatched gasshō-zukuri farmhouses built to shed heavy snow, is a UNESCO World Heritage Site and one of Japan’s iconic winter images. Nearby, the town of Takayama preserves a beautifully intact old merchant quarter, holds one of Japan’s grandest festivals with ornate floats, and is the home of marbled Hida beef. Gujō Hachiman is known for its summer-long folk dance and for crafting Japan’s realistic plastic food samples.',
      'On the rivers of the south, cormorant fishing (ukai) on the Nagara at Gifu City has continued for some 1,300 years, with fishermen using trained birds to catch sweetfish by torchlight. Gifu also has castle history (Nobunaga’s base) and good rail and expressway links to Nagoya, while its remote valleys offer abundant, affordable rural property.'
    ] },

  { en:'Shizuoka', kanji:'静岡', region:'Chūbu',
    short:'Pacific prefecture below Mt. Fuji — green tea and wasabi.',
    highlights:['Mt. Fuji’s south face','Most of Japan’s green tea','Real wasabi; Izu Peninsula','Eel; industry (instruments, motorcycles)'],
    long:[
      'Shizuoka stretches along the Pacific between Tokyo and Nagoya, with Mount Fuji rising along its northern border — the south side, including the classic view over the Miho pine grove and the sea, is quintessential Shizuoka. The mild coastal climate and abundant sunshine shape both its agriculture and lifestyle.',
      'It is Japan’s green-tea capital, producing a large share of the national crop on hillsides around Makinohara and the Abe River, and it grows much of the country’s real wasabi in clear mountain spring water. Lake Hamana is known for eel farming, and deep Suruga Bay yields delicacies such as raw sakura shrimp and deep-sea fish.',
      'The Izu Peninsula, jutting into the Pacific, is a popular resort region of hot springs, coastline and the onsen town of Atami, while Hakone’s slopes spill over from neighbouring Kanagawa. Shizuoka is also a manufacturing powerhouse — the home of Yamaha and Kawai pianos, Suzuki motorcycles and much more — giving it a solid economy alongside its scenery and within bullet-train reach of both Tokyo and Nagoya.'
    ] },

  { en:'Aichi', kanji:'愛知', region:'Chūbu',
    short:'Industrial heartland around Nagoya and Toyota.',
    highlights:['Nagoya, Japan’s 4th city','Toyota & manufacturing','Nagoya Castle, Atsuta Shrine','“Nagoya-meshi” cuisine'],
    long:[
      'Aichi, centred on Nagoya, is the industrial powerhouse of central Japan and the country’s manufacturing heartland. The Toyota Motor Corporation is based in the city that bears its name, and the wider region churns out cars, machinery, aerospace and ceramics, making Aichi one of Japan’s wealthiest and most productive prefectures.',
      'Nagoya is Japan’s fourth-largest city, a confident if business-minded metropolis with a reconstructed castle topped by golden shachihoko (tiger-fish) ornaments and the deeply revered Atsuta Shrine, said to house one of the imperial regalia. The area was the cradle of the warlords who unified Japan — Oda Nobunaga, Toyotomi Hideyoshi and Tokugawa Ieyasu all hailed from here.',
      'Aichi has a famously distinctive food culture, “Nagoya-meshi,” including miso-katsu, miso-simmered udon, hitsumabushi grilled eel and tebasaki chicken wings. It is well connected by bullet train and air (Chūbu Centrair airport) and, while the city is busy and built-up, the surrounding countryside and the Chita and Atsumi peninsulas offer quieter, more affordable living.'
    ] },

  { en:'Mie', kanji:'三重', region:'Kansai (Kinki)',
    short:'Home of the Ise Grand Shrine, pearls and Matsusaka beef.',
    highlights:['Ise Grand Shrine','Mikimoto cultured pearls','Matsusaka beef','Iga ninja; Suzuka circuit'],
    long:[
      'Mie occupies the eastern side of the Kii Peninsula, facing Ise Bay and the Pacific. Its spiritual heart, and Japan’s, is the Ise Grand Shrine (Ise Jingū) — the most sacred site in Shintō, dedicated to the sun goddess Amaterasu and ceremonially rebuilt from scratch every 20 years, a tradition reaching back over a millennium. The lively approach street of Okage Yokochō recreates an old pilgrimage town.',
      'The Shima Peninsula around Toba and Ago Bay is the birthplace of cultured pearls, pioneered by Mikimoto, and is still worked by the female ama free-divers who harvest shellfish. Inland, the city of Matsusaka gives its name to one of Japan’s most luxurious wagyu beefs, and the Iga region is famed as a cradle of the ninja, with a ninja museum and festival.',
      'Mie also has a sporty side — the Suzuka Circuit hosts the Japanese Formula 1 Grand Prix — and a wild, beautiful southern coast where the Kumano Kodō pilgrimage trails reach the sea. With good links to Nagoya and the Kansai cities, its towns and rural coast offer accessible, attractively priced property.'
    ] },

  { en:'Shiga', kanji:'滋賀', region:'Kansai (Kinki)',
    short:'Wrapped around Lake Biwa, Japan’s largest lake.',
    highlights:['Lake Biwa watersports & cycling','Original Hikone Castle','Enryaku-ji on Mt. Hiei (UNESCO)','Greener, cheaper neighbour of Kyoto'],
    long:[
      'Shiga is defined by Lake Biwa, Japan’s largest freshwater lake, which fills the centre of the prefecture and has shaped its life for centuries as a source of water, food and a historic trade route to Kyoto. The lake offers beaches, sailing, kayaking and a popular long-distance cycling route (the “Biwaichi”) around its shore.',
      'For all its proximity to Kyoto, Shiga keeps a calmer, greener character and notable history of its own. Hikone preserves one of only twelve original castle keeps in Japan, complete with its moat and the beloved mascot Hikonyan, and on Mount Hiei above the lake stands Enryaku-ji, the sprawling head temple of the Tendai Buddhist sect and a UNESCO World Heritage Site.',
      'The lakeside towns of Ōtsu and Nagahama, the “floating” island shrine of Chikubu, and well-preserved merchant streets reward exploration, while Shiga is also a quiet manufacturing base. With fast trains to Kyoto and Osaka but markedly cheaper housing, it appeals strongly to those who want Kansai access with more space and nature.'
    ] },

  { en:'Kyoto', kanji:'京都', region:'Kansai (Kinki)',
    short:'The thousand-year capital of temples and tradition.',
    highlights:['17 UNESCO sites','Kinkaku-ji, Kiyomizu-dera, Fushimi Inari','Geisha (Gion) & kaiseki cuisine','Tea ceremony & crafts'],
    long:[
      'Kyoto was Japan’s imperial capital for over a thousand years, from 794 until 1868, and remains the country’s cultural soul. Spared the worst of wartime bombing, the city preserves an extraordinary concentration of heritage — seventeen of its monuments are jointly inscribed as a UNESCO World Heritage Site — including the gold-leafed Kinkaku-ji, the wooden-stage temple of Kiyomizu-dera, the moss and rock gardens of the Zen temples, and the thousands of vermilion torii gates of Fushimi Inari.',
      'It is also the living home of refined traditional culture: the geiko and maiko (Kyoto’s geisha) of the Gion district, the tea ceremony, ikebana, Nishijin silk weaving, and multi-course kaiseki cuisine. Seasonal ritual — cherry blossoms along the Philosopher’s Path, autumn maples at Arashiyama and Tōfuku-ji — structures the year.',
      'Beyond the famous, crowded city, Kyoto Prefecture reaches north to a quiet, rural Sea of Japan coast, including the pine-covered sandbar of Amanohashidate (another of the “Three Views of Japan”) and the boathouse village of Ine. City property is expensive and tightly regulated to protect the townscape, but the northern districts offer far more affordable rural homes.'
    ] },

  { en:'Osaka', kanji:'大阪', region:'Kansai (Kinki)',
    short:'Japan’s kitchen and comedy capital — street food and energy.',
    highlights:['Street food: takoyaki, okonomiyaki','Dōtonbori & Osaka Castle','Comedy & friendly locals','Universal Studios Japan; Expo 2025'],
    long:[
      'Osaka is Japan’s boisterous second city and the commercial hub of the Kansai region. A merchant town for centuries — once “the nation’s kitchen,” where rice and goods were traded — it has a famously down-to-earth, humorous and outgoing culture, with its own dialect and a reputation for blunt friendliness.',
      'Food is central to its identity. Osaka is the home of takoyaki (octopus balls), okonomiyaki savoury pancakes and kushikatsu skewers, eaten along the neon-blazing canal of Dōtonbori beneath the famous Glico running-man sign. The city is also Japan’s comedy capital, the base of the manzai double-act tradition.',
      'Landmarks include the imposing reconstructed Osaka Castle, built by Toyotomi Hideyoshi, the Shinsekai retro district with Tsūtenkaku tower, and Universal Studios Japan. Osaka hosted World Expo 2025 on the reclaimed island of Yumeshima. A major transport nexus with its own international airport (Kansai), the city itself is dense and pricey, but it makes a high-energy, well-connected base for the whole Kansai region.'
    ] },

  { en:'Hyogo', kanji:'兵庫', region:'Kansai (Kinki)',
    short:'Two-coast prefecture — Kobe, Himeji Castle and onsen.',
    highlights:['Kobe city & Kobe beef','Himeji Castle (UNESCO)','Arima & Kinosaki onsen','Awaji Island & whirlpools'],
    long:[
      'Hyōgo is unusually varied, stretching from the Seto Inland Sea in the south all the way to the Sea of Japan in the north, with the big port city of Kobe as its capital. Kobe opened to foreign trade in the 19th century and retains a cosmopolitan flavour — a hillside of Western merchant houses, a Chinatown, and a stylish bayfront rebuilt after the devastating 1995 Great Hanshin earthquake. It gives its name, of course, to lavishly marbled Kobe beef.',
      'The prefecture’s crowning sight is Himeji Castle, the largest and finest surviving original castle in Japan, a brilliant-white hilltop fortress nicknamed the “White Heron” and a UNESCO World Heritage Site. Hot-spring lovers have two classics: ancient Arima Onsen tucked behind Kobe, and the willow-lined canal town of Kinosaki on the northern coast, made for strolling between bathhouses in a yukata.',
      'Awaji Island, linked by one of the world’s longest suspension bridges, guards the Naruto whirlpools and a gentle rural pace, while the northern “San’in” coast and the silver-grass plateau around Kamikōchi feel a world away from the Osaka-Kobe conurbation. That contrast means everything from city apartments to very cheap countryside homes.'
    ] },

  { en:'Nara', kanji:'奈良', region:'Kansai (Kinki)',
    short:'Japan’s first capital — sacred deer and the Great Buddha.',
    highlights:['Tōdai-ji Great Buddha','Free-roaming sacred deer','Kasuga Shrine (UNESCO)','Yoshino cherry blossoms'],
    long:[
      'Nara was Japan’s first permanent capital, founded in 710, and the place where Buddhism and a centralised Japanese state took root. That era left an astonishing legacy clustered in and around Nara Park, where the monuments are inscribed as a UNESCO World Heritage Site.',
      'The park’s centrepiece is Tōdai-ji, whose Great Buddha Hall — one of the world’s largest wooden buildings — houses a colossal bronze Buddha cast in the 8th century. Nearby stand the lantern-lined Kasuga Grand Shrine and the elegant Kōfuku-ji pagoda, and over a thousand sacred, free-roaming deer wander the grounds, bowing for biscuits. Hōryū-ji, to the southwest, preserves some of the oldest wooden buildings on Earth.',
      'Beyond the city, Nara is mountainous and rural. Yoshino is Japan’s most celebrated cherry-blossom mountain, clouded pink in spring, and the Ōmine range and Kumano routes draw pilgrims into rugged Shugendō country. Quiet, deeply historic and within commuting distance of Osaka and Kyoto, Nara combines heritage with comparatively affordable living once you leave the tourist core.'
    ] },

  { en:'Wakayama', kanji:'和歌山', region:'Kansai (Kinki)',
    short:'Spiritual Kii Peninsula — Kōyasan, Kumano and citrus.',
    highlights:['Kōya-san monasteries & Okunoin','Kumano Kodō pilgrimage (UNESCO)','Nachi Falls','Mikan oranges & ume plums'],
    long:[
      'Wakayama covers the south-western tip of the mountainous Kii Peninsula, a rugged, deeply spiritual and lightly populated prefecture facing the Pacific. Its religious sites form the core of the UNESCO “Sacred Sites and Pilgrimage Routes in the Kii Mountain Range.”',
      'High in the mountains, Kōya-san is the centre of Shingon Esoteric Buddhism, founded by the monk Kūkai in 816 — a monastic town of over a hundred temples where visitors can stay overnight, eat vegetarian shōjin cuisine and walk the lantern-lit Okunoin cemetery among towering cedars. The Kumano Kodō pilgrimage trails thread through the peninsula to the three grand Kumano shrines, one beside the 133-metre Nachi Falls, Japan’s tallest, framed by a vermilion pagoda.',
      'The mild coast is Japan’s leading producer of mikan oranges and ume plums, and offers rustic hot springs such as riverside Kawayu, the whale-watching town of Taiji and the resort of Shirahama. Sparsely settled and affordable, with strong migration-support programmes, Wakayama appeals to those drawn to nature, pilgrimage and a slow coastal-mountain life.'
    ] },

  { en:'Tottori', kanji:'鳥取', region:'Chūgoku',
    short:'Japan’s least-populous prefecture — famous sand dunes.',
    highlights:['Tottori Sand Dunes & Sand Museum','Detective Conan / Kitarō manga','Crab & pears','Mt. Daisen hiking & skiing'],
    long:[
      'Tottori is Japan’s least-populous prefecture, a quiet strip along the Sea of Japan coast backed by mountains. Its most famous sight is unexpected: the Tottori Sand Dunes, a sweeping expanse of wind-sculpted sand stretching along the shore, where visitors can sandboard, ride camels or paraglide, and an adjacent Sand Museum displays astonishing large-scale sand sculptures.',
      'The prefecture punches above its weight in manga heritage. It is the birthplace of Gōshō Aoyama, creator of “Detective Conan,” and of Shigeru Mizuki, whose yōkai-monster classic “GeGeGe no Kitarō” fills a themed street of bronze statues in Sakaiminato. Both draw dedicated fans.',
      'Mount Daisen, a striking volcano sometimes called the “Mount Fuji of the west,” offers hiking in summer and skiing in winter, while the coast yields celebrated snow crab and the inland orchards produce the famous Nijisseiki “twentieth-century” pears. With abundant nature, very low population pressure and inexpensive housing, Tottori is among the most rural and affordable corners of Honshū.'
    ] },

  { en:'Shimane', kanji:'島根', region:'Chūgoku',
    short:'Remote, myth-steeped prefecture of ancient shrines.',
    highlights:['Izumo Taisha grand shrine','Matsue, the “water city”','Iwami Ginzan silver mine (UNESCO)','Oki Islands geopark'],
    long:[
      'Shimane is a remote, elongated prefecture on the Sea of Japan coast, rich in mythology and among the least-visited parts of Honshū — which is part of its appeal. It is central to Japan’s creation myths: Izumo Taisha is one of the oldest and most important Shintō shrines, dedicated to the deity of marriage and good relationships, and tradition holds that all of Japan’s gods gather here each autumn.',
      'The castle town of Matsue, set between a lake and a lagoon and known as the “water city,” keeps one of Japan’s twelve original castle keeps and the former home of writer Lafcadio Hearn, who helped introduce Japan to the West. Nearby, the Adachi Museum of Art is famous for gardens regularly judged the best in Japan.',
      'In the west, the Iwami Ginzan silver mine — once one of the world’s great sources of silver — is a UNESCO World Heritage Site with atmospheric old mining towns, and the region preserves the dynamic Iwami Kagura sacred dance. Offshore, the Oki Islands form a UNESCO Global Geopark. Sparsely populated and inexpensive, Shimane suits those seeking deep tradition and tranquillity.'
    ] },

  { en:'Okayama', kanji:'岡山', region:'Chūgoku',
    short:'Sunny prefecture of gardens, peaches and canal-town Kurashiki.',
    highlights:['Kōraku-en (top-3 garden)','Kurashiki Bikan canal district','White peaches & Muscat grapes','Momotarō legend'],
    long:[
      'Okayama, facing the calm Seto Inland Sea, markets itself as the “Land of Sunshine” for its notably low rainfall — a mild, stable climate that has long favoured fruit growing and comfortable living. It is a convenient bullet-train hub and the mainland gateway to Shikoku via the Seto Ōhashi bridge.',
      'Okayama City’s Kōraku-en is counted among the three great landscape gardens of Japan, a spacious riverside garden designed to be strolled, set against the black-walled “Crow Castle.” A short hop away, the Bikan historic quarter of Kurashiki is a postcard of white-walled storehouses along a willow-lined canal, now filled with cafés, craft shops and the respected Ōhara Museum of Art.',
      'The sunny climate yields prized white peaches and large, sweet Muscat and Pione grapes. Okayama also claims the legend of Momotarō, the “Peach Boy” who set out from here to defeat ogres, a story woven into local branding. Art islands such as Inujima lie just offshore. With good transport, gentle weather and affordable property inland, it is an easygoing place to settle.'
    ] },

  { en:'Hiroshima', kanji:'広島', region:'Chūgoku',
    short:'Prefecture of remembrance and the floating Miyajima torii.',
    highlights:['Peace Memorial & A-Bomb Dome (UNESCO)','Miyajima / Itsukushima torii (UNESCO)','Hiroshima-style okonomiyaki','Seto Inland Sea oysters'],
    long:[
      'Hiroshima, the largest city of the Chūgoku region, carries one of the most significant histories of the 20th century. On 6 August 1945 it became the first city destroyed by an atomic bomb; today the Peace Memorial Park, the preserved skeletal A-Bomb Dome (a UNESCO World Heritage Site) and the moving Peace Memorial Museum stand as a global plea for nuclear abolition, while the rebuilt, green and welcoming city is a powerful symbol of recovery.',
      'Just offshore, the sacred island of Miyajima is home to Itsukushima Shrine and its great vermilion torii gate that appears to float on the sea at high tide — another UNESCO site and one of Japan’s most iconic images, watched over by tame deer and the forested peak of Mount Misen.',
      'The prefecture is also a food destination: Hiroshima-style okonomiyaki, layered with noodles and cooked on a griddle, and the plump oysters farmed in the Inland Sea, of which Hiroshima is Japan’s leading producer. Inland lie the gorges of Sandankyō and historic castle towns, while the Inland Sea coast and islands — linked by the Shimanami Kaidō cycling route — offer mild weather and increasingly popular small-town living.'
    ] },

  { en:'Yamaguchi', kanji:'山口', region:'Chūgoku',
    short:'Honshū’s western tip — caves, fugu and a famous bridge.',
    highlights:['Akiyoshidō limestone cavern','Fugu (pufferfish) in Shimonoseki','Kintai-kyō arched bridge','Meiji Restoration history'],
    long:[
      'Yamaguchi forms the western tip of Honshū, almost touching Kyūshū across the narrow Kanmon Strait. It has an outsized place in modern Japanese history: the old Chōshū domain based here was a driving force of the 1868 Meiji Restoration that ended the shogunate, and the prefecture has produced more prime ministers than any other.',
      'Its natural showpiece is the Akiyoshidai plateau, a rolling expanse of limestone grassland beneath which lies Akiyoshidō, Japan’s largest limestone cavern, walkable for nearly a kilometre past vast stone formations and underground pools. At Iwakuni, the elegant five-arched wooden Kintai-kyō bridge spans the Nishiki River below a hilltop castle.',
      'Shimonoseki, at the strait, is Japan’s capital of fugu (pufferfish), the delicacy that must be prepared by licensed chefs, and a historic port. The seaside shrine of Motonosumi, with its long row of red torii above the sea, and the castle town of Hagi, where the Restoration’s thinkers studied, round out a prefecture that mixes scenery, history and excellent seafood with low population pressure.'
    ] },

  { en:'Tokushima', kanji:'徳島', region:'Shikoku',
    short:'East Shikoku — Awa Odori dance and Naruto whirlpools.',
    highlights:['Awa Odori dance festival','Naruto tidal whirlpools','Iya Valley vine bridges','Indigo dyeing & sudachi citrus'],
    long:[
      'Tokushima occupies the eastern corner of Shikoku, facing the Kii Channel and joined to Honshū by bridges via Awaji Island. It is best known for the Awa Odori, the largest and most famous traditional dance festival in Japan: every August, hundreds of thousands of dancers and spectators fill the streets to the chant that “the dancers are fools and the watchers are fools, so you might as well dance.”',
      'Where the tides rush through the Naruto Strait, giant whirlpools form that can be viewed from boats or a glass-floored walkway beneath the bridge. Deep in the interior, the remote Iya Valley is one of Japan’s great hidden regions, with steep gorges, hot springs and centuries-old vine suspension bridges once used by fleeing samurai.',
      'Historically wealthy from indigo (ai) dyeing, Tokushima still produces the rich blue dye, and its sunny climate yields the tart sudachi citrus used across Japanese cooking. The prefecture is also a starting point for the 88-temple Shikoku pilgrimage. Rural, scenic and inexpensive, it has been a notable pioneer in attracting remote workers and reviving mountain villages.'
    ] },

  { en:'Kagawa', kanji:'香川', region:'Shikoku',
    short:'Japan’s smallest prefecture — udon and art islands.',
    highlights:['Sanuki udon','Naoshima & Teshima art islands','Ritsurin-kōen garden','Kotohira-gū shrine; Shōdoshima olives'],
    long:[
      'Kagawa, on the Seto Inland Sea side of Shikoku, is the smallest of Japan’s prefectures but densely packed with attractions. It is so devoted to its chewy Sanuki udon noodles that it has unofficially rebranded itself the “Udon Prefecture,” with hundreds of specialist shops, some self-service, drawing noodle pilgrims from across the country.',
      'The calm island-studded sea here is the stage for the acclaimed Setouchi Triennale art festival, and islands such as Naoshima and Teshima have become world-famous for their museums and installations — including Tadao Andō’s concrete galleries and Yayoi Kusama’s polka-dot pumpkins — turning sleepy fishing islands into pilgrimage sites for contemporary art.',
      'On the mainland, Takamatsu’s Ritsurin-kōen is one of Japan’s most beautiful strolling gardens, and the hilltop shrine of Kotohira-gū (“Konpira-san”) rewards a long stone stairway climb. Shōdoshima island is known for olives and soy sauce. Compact, mild and well connected, Kagawa offers easy island-hopping and accessible small-town life.'
    ] },

  { en:'Ehime', kanji:'愛媛', region:'Shikoku',
    short:'Citrus country with Japan’s oldest hot spring.',
    highlights:['Dōgo Onsen (ancient bathhouse)','Mikan & many citrus varieties','Matsuyama Castle','Shimanami Kaidō cycling route'],
    long:[
      'Ehime spreads along the north-western coast of Shikoku, facing the Seto Inland Sea, with the regional city of Matsuyama as its capital. Matsuyama crowns a central hill with one of Japan’s twelve surviving original castles and is home to Dōgo Onsen, reputed to be the oldest hot spring in Japan, whose grand 1894 bathhouse is said to have inspired the bathhouse in the film “Spirited Away.”',
      'The mild climate makes Ehime Japan’s citrus heartland: beyond ordinary mikan, it grows an astonishing range of varieties — iyokan, dekopon, setoka and more — and citrus flavours everything from juice to sweets. The literary heritage is strong too, as the setting of Natsume Sōseki’s classic novel “Botchan.”',
      'For cyclists, the Shimanami Kaidō is a highlight of any visit: a roughly 70-kilometre route on dedicated paths that hops across a chain of beautiful islands and great suspension bridges from Imabari over to Onomichi in Hiroshima. With seaside towns, citrus groves and a relaxed pace, Ehime offers appealing and affordable Inland Sea living.'
    ] },

  { en:'Kochi', kanji:'高知', region:'Shikoku',
    short:'Wild Pacific south — bonito, a clear river and Ryōma.',
    highlights:['Seared bonito (katsuo)','Clear Shimanto River','Sakamoto Ryōma','Capes of Muroto & Ashizuri'],
    long:[
      'Kōchi sweeps along the entire Pacific south of Shikoku, a long, mountainous and thinly populated prefecture with a famously open, independent character forged by its exposure to the open ocean. It is one of Japan’s rainiest regions and one of its most rural.',
      'Its signature dish is katsuo no tataki — bonito seared over a straw fire so the outside is smoky and the inside raw — eaten with garlic and citrus, and best at the lively Hirome Market in Kōchi City. The Shimanto River, often called Japan’s last clear (dam-free) major river, winds through the countryside crossed by low “sinking bridges” designed to submerge in floods, and is a paradise for canoeing and cycling.',
      'Kōchi City keeps one of the twelve original castles, and the prefecture is proud of native son Sakamoto Ryōma, the charismatic samurai reformer who helped engineer the fall of the shogunate; his statue gazes out to sea at Katsurahama. The dramatic capes of Muroto and Ashizuri mark its wild coastline. Remote and inexpensive, Kōchi rewards those seeking nature, surf and an unhurried life.'
    ] },

  { en:'Fukuoka', kanji:'福岡', region:'Kyūshū & Okinawa',
    short:'Kyūshū’s gateway city — ramen and street-food stalls.',
    highlights:['Hakata tonkotsu ramen','Yatai street-food stalls','Yamakasa festival; Dazaifu shrine','Youthful, fast-growing hub'],
    long:[
      'Fukuoka is the largest city of Kyūshū and the gateway to the southern island, a youthful, fast-growing and famously livable place that is geographically closer to Seoul and Shanghai than to Tokyo. Compact and energetic, with beaches, mountains and an airport all close to the centre, it regularly ranks among Japan’s most attractive cities for young people and startups.',
      'It is a food lover’s city above all. Fukuoka is the home of Hakata-style tonkotsu ramen — thin noodles in a rich, milky pork-bone broth — and of the yatai, open-air street-food stalls that line the riverbanks and Nakasu island after dark, serving ramen, grilled skewers and more in convivial clusters found nowhere else in Japan at this scale.',
      'Tradition endures in the Hakata Gion Yamakasa festival, where teams race heavy ornate floats through the streets, and just outside the city the Dazaifu Tenmangū shrine honours the deity of learning amid plum trees. With strong rail links across Kyūshū and to Honshū via bullet train, Fukuoka makes a dynamic, relatively affordable base in the south.'
    ] },

  { en:'Saga', kanji:'佐賀', region:'Kyūshū & Okinawa',
    short:'Small craft prefecture — the cradle of Japanese porcelain.',
    highlights:['Arita, Imari & Karatsu porcelain','Asia’s largest balloon fiesta','Yoshinogari Yayoi site','Ureshino tea & onsen'],
    long:[
      'Saga is a small, quiet prefecture in north-western Kyūshū, often passed through between Fukuoka and Nagasaki but rewarding for those who stop. Its great claim to fame is ceramics: in the early 1600s, Korean potters discovered porcelain clay here, and the towns of Arita, Imari and Karatsu have produced fine porcelain ever since — Arita ware was among Japan’s first major exports to Europe, and the kiln towns remain centres of the craft.',
      'Each autumn the skies above the Kase River fill with colour during the Saga International Balloon Fiesta, the largest hot-air-balloon competition in Asia. The Yoshinogari Historical Park preserves one of Japan’s most important Yayoi-period sites, a large moated settlement with reconstructed watchtowers and dwellings offering a window onto life two millennia ago.',
      'Saga also has appealing hot springs — Ureshino, known for skin-softening waters and green tea, and seaside Takeo with its ancient camphor tree and striking library. With fertile plains, a mild climate and very modest property prices, this understated prefecture suits those after craft heritage and a calm rural pace.'
    ] },

  { en:'Nagasaki', kanji:'長崎', region:'Kyūshū & Okinawa',
    short:'Cosmopolitan port shaped by foreign trade and history.',
    highlights:['Dejima & foreign-trade history','Hidden Christian sites (UNESCO)','Peace Park & A-bomb history','Glover Garden; Huis Ten Bosch'],
    long:[
      'Nagasaki, on the western edge of Kyūshū, is among Japan’s most cosmopolitan and historically layered prefectures, shaped by centuries of contact with the outside world. During Japan’s long period of isolation, the artificial island of Dejima in Nagasaki harbour was the country’s only window onto European (Dutch) trade, leaving a unique blend of cultures still visible in the city’s Chinatown, churches and hillside Glover Garden of Western merchant houses.',
      'That history includes a hidden Christian community that kept its faith in secret for over two centuries; the related churches and sites across the region are inscribed as a UNESCO World Heritage Site. Nagasaki was also the target of the second atomic bomb in August 1945, and its Peace Park and museum, like Hiroshima’s, are dedicated to remembrance and the abolition of nuclear weapons.',
      'The prefecture is overwhelmingly maritime, with countless islands, the former coal-mining island of Hashima (“Battleship Island”), and the dense night view over the harbour, rated one of Japan’s finest. The European-themed resort of Huis Ten Bosch adds a quirky note. Scenic, distinctive and affordable, Nagasaki offers island and coastal living steeped in history.'
    ] },

  { en:'Kumamoto', kanji:'熊本', region:'Kyūshū & Okinawa',
    short:'Castle town beside the vast Mt. Aso volcanic caldera.',
    highlights:['Kumamoto Castle','Mt. Aso caldera & grasslands','Pure spring water; basashi','Mascot Kumamon'],
    long:[
      'Kumamoto sits in the centre of Kyūshū and is dominated by two icons: its great castle and its great volcano. Kumamoto Castle, built in the early 1600s, is one of Japan’s most impressive fortresses, famous for its steep “musha-gaeshi” stone walls; badly damaged in the 2016 earthquakes, it has been undergoing a long, carefully staged restoration that is itself a draw.',
      'To the east lies Mount Aso, one of the largest active volcanic calderas in the world — a vast bowl, dozens of kilometres across, containing towns, farms and grasslands, with steaming craters at its centre. The surrounding highlands offer dramatic scenery, grazing cattle and hot springs such as Kurokawa Onsen, a beloved cluster of rustic riverside baths.',
      'Blessed with abundant pure spring water from the volcanic terrain, Kumamoto is proud of its water, its produce and unusual local foods like basashi (horse-meat sashimi). Its wildly popular black-bear mascot, Kumamon, has become a national marketing phenomenon. With rich nature, good water and modest prices, the prefecture is an attractive base in central Kyūshū.'
    ] },

  { en:'Oita', kanji:'大分', region:'Kyūshū & Okinawa',
    short:'Japan’s “onsen prefecture” — Beppu and Yufuin.',
    highlights:['Most hot springs in Japan','Beppu’s “hells”','Chic, artsy Yufuin','Kunisaki Buddhist sites; kabosu'],
    long:[
      'Ōita, in north-eastern Kyūshū, is Japan’s undisputed hot-spring capital, with more thermal sources and a greater volume of hot water than any other prefecture — the volcanic landscape steams almost everywhere. Beppu is the most famous onsen town, where columns of steam rise over the rooftops and the “hells” (jigoku) are vividly coloured, boiling ponds meant for viewing rather than bathing, from cobalt blue to blood red.',
      'A short way inland, Yufuin offers a more refined, artsy alternative: a relaxed resort village of boutique inns, galleries and cafés set beneath the twin-peaked Mount Yufu, popular for upscale day trips and overnight stays. Together the two define Ōita’s spa-resort identity.',
      'The Kunisaki Peninsula preserves an ancient Buddhist culture of stone carvings, cliffside temples and the Usa shrine, the head of thousands of Hachiman shrines nationwide. The prefecture is also known for kabosu, a tart green citrus used across Japanese cooking, and toriten chicken tempura. Scenic, restorative and reasonably priced, Ōita rewards those who love hot springs and quiet countryside.'
    ] },

  { en:'Miyazaki', kanji:'宮崎', region:'Kyūshū & Okinawa',
    short:'Sunny southeast coast of myth, surfing and mangoes.',
    highlights:['Takachiho Gorge & mythology','Nichinan coast surfing; Aoshima','Mangoes & Hyūganatsu citrus','Miyazaki wagyu beef'],
    long:[
      'Miyazaki runs down the sunny south-eastern coast of Kyūshū, a warm, laid-back prefecture of beaches, palms and surf that once thrived as a honeymoon destination and still feels like Japan’s mellow Pacific edge. Its long coastline and reliable swell make it one of the country’s top surfing regions.',
      'It is also a land of myth. Takachiho Gorge, a sheer, mossy ravine with a waterfall best seen by rowboat, is bound up with Japan’s founding legends — the area is associated with the sun goddess Amaterasu and the divine descent of the imperial line, celebrated in nightly kagura sacred dances. On the coast, the small shrine-island of Aoshima is ringed by the curious “devil’s washboard” rock formations.',
      'The warm climate yields luxury produce, including famously sweet (and expensive) Miyazaki mangoes and Hyūganatsu citrus, while Miyazaki wagyu beef has won top national prizes. Cedar forestry is a major industry inland. Affordable, sunny and unhurried, Miyazaki appeals to those drawn to surf, nature and a gentle climate.'
    ] },

  { en:'Kagoshima', kanji:'鹿児島', region:'Kyūshū & Okinawa',
    short:'Volcano-side prefecture of Satsuma history and islands.',
    highlights:['Sakurajima volcano','Satsuma domain history','Sweet-potato shōchū','Yakushima cedars (UNESCO); Tanegashima space'],
    long:[
      'Kagoshima occupies the southern tip of Kyūshū and lives in the company of a volcano: Sakurajima, one of the world’s most active, looms across the bay from the city and frequently dusts it with ash, earning Kagoshima the nickname the “Naples of the East.” The bayfront city is warm, palm-lined and proud of its hot-sand baths at nearby Ibusuki.',
      'Historically this was the powerful Satsuma domain, whose forward-looking samurai — figures like Saigō Takamori — were instrumental in toppling the shogunate and modernising Japan in the 19th century, importing Western technology early. That legacy of independence still colours local identity, along with sweet-potato shōchū (the prefecture’s signature spirit), black pork and the bright local cuisine.',
      'Kagoshima reaches far out to sea through a chain of islands. Yakushima, cloaked in ancient cedar forest and rainforest, is a UNESCO natural World Heritage Site and a hikers’ pilgrimage, while Tanegashima hosts Japan’s main space launch centre. With volcanic scenery, subtropical warmth and remote islands, it offers some of the country’s most distinctive — and affordable — settings.'
    ] },

  { en:'Okinawa', kanji:'沖縄', region:'Kyūshū & Okinawa',
    short:'Subtropical islands with distinct Ryūkyū culture.',
    highlights:['Coral reefs & white beaches','Ryūkyū culture & Shuri Castle','Famous longevity & cuisine','Complex WWII / US-base history'],
    long:[
      'Okinawa is Japan’s southernmost prefecture, a long arc of subtropical islands strung across the sea between Kyūshū and Taiwan. Warm year-round, ringed by coral reefs and white-sand beaches, it is the country’s premier destination for diving, snorkelling and island holidays, with the main island anchored by the city of Naha.',
      'Until the 19th century these islands were the independent Ryūkyū Kingdom, a seafaring trading state with its own language, religion, music (the sanshin lute), dance, textiles and architecture — a heritage still strongly felt and symbolised by Shuri Castle in Naha (currently being rebuilt after a 2019 fire). Okinawan cuisine, from gōyā champurū to pork dishes, is part of a lifestyle long linked to world-famous longevity.',
      'That distinctiveness comes with a heavy modern history: Okinawa was the site of one of the bloodiest battles of World War II, and it hosts a large concentration of US military bases, a continuing source of local debate. Beyond the busy main island lie quieter gems — Ishigaki, Iriomote’s jungle and the Miyako islands. The climate, culture and beaches make it unique within Japan, though island property and logistics carry their own considerations.'
    ] },
];

window.PREF_REGION_ORDER = ['Hokkaidō','Tōhoku','Kantō','Chūbu','Kansai (Kinki)','Chūgoku','Shikoku','Kyūshū & Okinawa'];
window.prefSlug = (en) => en.toLowerCase().replace(/ /g,'-');
window.prefWiki = (en) => en==='Hokkaido' ? 'https://en.wikipedia.org/wiki/Hokkaido'
  : en==='Tokyo' ? 'https://en.wikipedia.org/wiki/Tokyo'
  : 'https://en.wikipedia.org/wiki/' + en.replace(/ /g,'_') + '_Prefecture';
