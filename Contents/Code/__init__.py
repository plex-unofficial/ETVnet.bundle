# -*- coding: utf-8 -*-
import re,urllib2,base64
#, translit, urllib
# eTV Plugin
# by Alex Titoff
# http://rozdol.com/
# rozdol@gmail.com
VERSION						= 2.5
####################################################################################################
# v2.5 - March 20, 2011
# > Drill-in 
#
# v2.4 - March 1, 2011
# > Update check improved 
#
# v2.3 - February 28, 2011
# > List of viewed videos 
#
# v2.2 - February 28, 2011
# > Favorites, Account info 
#
# v2.1 - February 28, 2011
# > Login reprogrammed 
#
# v2.0 - February 26, 2011
# > Framework V.2 used 
# > Version update check
# > Page numbering
# > Options for bitrates, free smple and alternate server.
#
# v1.3 - February 24, 2011
# > Browsing reprpogrammed 
#
# v1.2 - February 23, 2011
# > Added Bitrate auto decrease, Pagination, Hide categories option, Sorting 
#
# v1.1 - February 22, 2011
# > Added Category Browser, Thumbs
#
# v1.0 - February 21, 2011
# > Complete rewrite of plugin according to API/2.0
#
# v0.2 - January 22, 2011
# > Changed default icon
#
# v0.1 - January 20, 2011
# > Initial release
#
###################################################################################################
VIDEO_PREFIX				= "/video/etvnet2"
NAME						= 'eTVnet2'
ART							= 'art-default.jpg'
ICON						= 'icon-default.png'
PREFS						= 'icon-prefs.png'
API_URL						= 'http://etvnet.com/api/v2.0/'
BASE_URL					= 'http://etvnet.com/'
USER_AGENT					= 'User-Agent','PLEX eTVnet plugin (Macintosh; U; Intel Mac OS X 10.6; ru; rv:1.9.2.13) Author/Alex_Titov'
LOGGEDIN					= False
sessionid					= ''
title1						= NAME
title2						= ''
SORT_NAMES 					= ['По эфиру', 'По году', 'Но названию', 'По рейтингу']
SORT_VALUES 				= ['on_air','production_year','name','mark_total']
DIR_NAMES 					= ['По убыванию', 'По возрастанию']
DIR_VALUES 					= ['desc','asc'] 
UPDATECHECK_URL            = 'http://www.rozdol.com/versioncheck.php?module=etvnet&v='+ str(VERSION)+'&info=' 
####################################################################################################

def Start():


	Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, NAME, ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	MediaContainer.title1 = title1
	MediaContainer.title2 = title2
	MediaContainer.viewGroup = "List"
	MediaContainer.art = R(ART)
	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)
	HTTP.CacheTime = CACHE_1HOUR
	#HTTP.Headers['User-Agent'] = USER_AGENT
	HTTP.Headers['User-Agent']='Mozilla/5.0 [Macintosh; U; Intel Mac OS X 10.6; ru; rv:1.9.2.13] Gecko/20101203 Firefox/3.6.13 GTB7.1'
	HTTP.Headers['Accept']='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HTTP.Headers['Accept-Encoding']='gzip,deflate,sdch'
	HTTP.Headers['Accept-Language']='ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3'
	HTTP.Headers['Accept-Charset']='windows-1251,utf-8;q=0.7,*;q=0.7'
	HTTP.Headers['Keep-Alive']='115'
	HTTP.Headers['Referer']='http://etvnet.com/'
	#LOGGEDIN = Login()
	
####################################################################################################

def ValidatePrefs():
	global LOGGEDIN, sessionid
	u = Prefs['username']
	p = Prefs['password']
	if( u and p ):
		LOGGEDIN = Login()
		if LOGGEDIN == False:
			return MessageContainer(
				"Ошибка",
				"Отказ в доступе"
			)
	else:
		return MessageContainer(
			"Ошибка",
			"Веедите имя и пароль"
		)

####################################################################################################

def MainMenu():
	global LOGGEDIN, sessionid
	httpCookies=HTTP.GetCookiesForURL(BASE_URL)
	url=API_URL +'channel_list.json'
	try:
		obj=JSON.ObjectFromURL(url)
		LOGGEDIN = True
		msg=''
	except:
		LOGGEDIN = Login()
		Log(" --> FROM MAIN1! %s SSID='%s'" % (LOGGEDIN,httpCookies))
		msg='(Введите привильные параметры входа)'
		
	Log(" --> FROM MAIN! %s SSID='%s'" % (LOGGEDIN,sessionid))
	dir = MediaContainer(viewGroup="List", noCache=True, httpCookies=httpCookies)
	if Prefs['updates'] == True and CheckForUpdate() != None:
		newver=CheckForUpdate()
		dir.Append(Function(DirectoryItem(UpdateAvailable, title='Доступна новая версия '+str(newver), thumb=R('warning.png'))))
	if LOGGEDIN == True:
		dir.Append(Function(DirectoryItem(Channels, title='Каналы'), link='channel_list.json'))
		if Prefs['hidecat']==False:
			dir.Append(Function(DirectoryItem(Categories, title='Каталог', thumb=R('folder.png')), link='catalog.json?', page=1))
		dir.Append(Function(InputDirectoryItem(Search, title='Поиск', prompt=L('SEARCHPROMT'), thumb=R('search.png'))))
		dir.Append(Function(DirectoryItem(Categories, title='Избранное', thumb=R('Favorites.png')), link='media/bookmarks.json?', page=1))
		dir.Append(Function(DirectoryItem(GetViewedList, title='Мои просмотры', thumb=R('list.png'))))
		dir.Append(Function(DirectoryItem(GetAccountInfo, title='Мои данные', thumb=R('info.png'))))
	dir.Append(PrefsItem('Настройки '+msg, thumb=R(PREFS)))
	dir.Append(Function(DirectoryItem(About, title='О плагине', thumb=R('info.png'))))
	return dir

####################################################################################################

def Channels(sender,link):
	url=API_URL + link
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2='Каналы')
	obj = JSON.ObjectFromURL(url, encoding='utf-8')
	sortby=''
	sortdir=''
	index = SORT_NAMES.index(Prefs['sort'])
	sortby= SORT_VALUES[index]
	index = DIR_NAMES.index(Prefs['direction'])
	sortdir= DIR_VALUES[index]
	for item in obj:
		slug=item['slug']
		link='channel/'+str(slug)+".json"+"?per_page="+Prefs['perpage']+"&sort="+sortby+"&dir="+sortdir
		title=item['name']
		dir.Append(Function(DirectoryItem(Categories, title=title,thumb=R(slug+'.jpg')), link=link, page=1,chslug=slug))
	return dir

####################################################################################################

def Categories(sender,link,page,chslug=""):
	sortby=''
	sortdir=''
	index = SORT_NAMES.index(Prefs['sort'])
	sortby = SORT_VALUES[index]
	index = DIR_NAMES.index(Prefs['direction'])
	sortdir = DIR_VALUES[index]
	thumb=''
	nextpage=page+1
	prevpage=page-1
	url=API_URL + link
	i=0
	if page>0:
		url=url + "&page="+str(page)
	if url.find('?q=') > 0:
		title2="Результаты"
	else:
		title2=sender.itemTitle
	category=title2
	indx=title2.find(' ->')
	if indx>0:
		category=title2[0:indx]
	c = ContextMenu(includeStandardItems=False)
	c.Append(Function(DirectoryItem(AddToFavorites, title='Добавить в избранное')))
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2=title2, contextMenu=c)
	#if page>1:
	#	dir.Append(Function(DirectoryItem(Categories, title=L('PREVPAGE'),thumb=R('previous.png')), link=link, page=prevpage))
	obj=JSON.ObjectFromURL(url)
	if obj.has_key('header'):
		currpage=obj['header']['page_info']['current']
		totpages=obj['header']['page_info']['total']
	else:
		currpage=0
		totpages=0
	title2=title2+' '+str(currpage)+'/'+str(totpages)
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2=title2)
	if (Prefs['hidecat']==False and obj.has_key('header')):
		if obj['header'].has_key('categories'):
			for item in obj['header']['categories']:
				linktoday='catalog/'+str(item['slug'])+'.json?'
				if chslug!="":
					linktoday='channel/'+chslug+'/'+str(item['slug'])+'.json?'
				title=item['name']
				count=item['count']
				Log("----> Category='%s'" % (title))
				dir.Append(Function(DirectoryItem(Categories, title=title+'('+str(count)+')'), link=linktoday, page=1))	
	if obj.has_key('results'):
		for item in obj['results']:
			id=item['id']
			title=item['name']
			vcalss=item['class']
			summary= 'Продолжительность минут: '+str(item['duration']) + '\n'+'B эфире '+item['on_air']
			rating=item['mark_total']
			subtitle=''#'B эфире '+item['on_air']
			slug=str(item['slug'])
			Log("----> Resuts='%s'" % (title))
			linktoday="media/details/"+str(id)+".json?"
			duration=item['duration']*6000
			if Prefs['usedetails']==True:
				dataurl=API_URL +"media/details/"+str(id)+".json"
				obj2=JSON.ObjectFromURL(dataurl)
				summary=bj2['media']['description']
				thumb=obj2['media']['screenshots_path']+'b01.jpg'
			else:
				thumb='http://static.etvnet.com/shared/image/media/'+str(id)+'/'+slug+'.jpg'
			dir.Append(Function(DirectoryItem(MediaInfo, title=title, subtitle=subtitle, summary=summary, thumb=Function(Thumb, url=thumb), duration=duration,rating=rating), id=id, page=1))
	if obj.has_key('bookmarks'):
		for item in obj['bookmarks']:
			id=item['media']['id']
			title=item['media']['name']
			vcalss=item['media']['is_container']
			added=['added']
			summary= 'Добавлен: '+str(item['added']) + '\n'+'B эфире '+item['media']['on_air']
			rating=item['media']['mark_total']
			subtitle=''#'B эфире '+item['on_air']
			Log("----> Resuts='%s'" % (title))
			linktoday="media/details/"+str(id)+".json?"
			duration=0
			if Prefs['usedetails']==True:
				dataurl=API_URL +"media/details/"+str(id)+".json"
				obj2=JSON.ObjectFromURL(dataurl)
				summary=bj2['media']['description']
				thumb=obj2['media']['screenshots_path']+'b01.jpg'
			else:
				thumb=''
			dir.Append(Function(DirectoryItem(MediaInfo, title=title, subtitle=subtitle, summary=summary, thumb=Function(Thumb, url=thumb), duration=duration,rating=rating), id=id, page=1))
	
	if currpage!=totpages:
		dir.Append(Function(DirectoryItem(Categories, title=category+' -> Страница '+str(nextpage),thumb=R('next.png')), link=link, page=nextpage))
	return dir

####################################################################################################

def MediaInfo(sender,id, page):
	nextpage=page+1
	prevpage=page-1
	origid=id	
	url=API_URL +"media/details/"+str(id)+".json?page="+str(page)
	c = ContextMenu(includeStandardItems=False)
	c.Append(Function(DirectoryItem(AddToFavorites, title='Добавить в избранное')))
	#dir = MediaContainer(viewGroup='Details', title2=title, contextMenu=c)
	dir = MediaContainer(viewGroup='Details', httpCookies=HTTP.GetCookiesForURL(BASE_URL), title2=sender.itemTitle, contextMenu=c)
	obj=JSON.ObjectFromURL(url)
	thumb=obj['media']['screenshots_path']+'b01.jpg'
	summary=obj['media']['description']
	vclass=obj['media']['class']
	rating=obj['media']['mark_total']
	duration=obj['media']['duration']
	title=obj['media']['name']
	title2=title
	subtitle=obj['media']['on_air']
	if vclass == 'Container':
		currpage=obj['media']['children_page_info']['current']
		totpages=obj['media']['children_page_info']['total']
		title2=title2+' '+str(currpage)+'/'+str(totpages)
		dir.title2=title2
		if page>1:
			dir.Append(Function(DirectoryItem(MediaInfo, title=L('PREVPAGE'),thumb=R('previous.png')), id=origid, page=prevpage))
		for channel in obj['children']:
			id=channel['id']
			title=channel['name']
			subtitle=channel['on_air']
			rating=channel['mark_total']
			#thumb='http://static.etvnet.com/shared/image/media/'+str(id)+'/'+slug+'.jpg'
			thumb=''
			dir.Append(Function(DirectoryItem(MediaInfo, title=title, subtitle=subtitle, summary=summary, thumb=Function(Thumb, url=thumb), rating=rating), id=id, page=1))
		if currpage!=totpages:
			dir.Append(Function(DirectoryItem(MediaInfo, title=L('NEXTPAGE'),thumb=R('next.png')), id=origid, page=nextpage))
	else:
		pic=Function(Thumb, url=thumb)
		bitrates=obj['media']['bitrates']
		for item in bitrates:
			bitrate=item
			Log("----> BitRate='%s'" % (bitrate))
			url=API_URL +"media/watch/"+str(id)+"/"+str(bitrate)+".json?is_preview=0&other_server=0"
			dir.Append(Function(WindowsMediaVideoItem(PlayMedia, title=str(bitrate)+'kbs, '+title, subtitle=str(bitrate)+'kbs', summary=summary,thumb=pic,rating=rating, duration=duration), url=url))
			url=API_URL +"media/watch/"+str(id)+"/"+str(bitrate)+".json?is_preview=1&other_server=0"
			dir.Append(Function(WindowsMediaVideoItem(PlayMedia, title=str(bitrate)+'kbs, '+title, subtitle="Бесплатный отрывок", summary=summary,thumb=pic,rating=rating, duration=duration),url=url))
			url=API_URL +"media/watch/"+str(id)+"/"+str(bitrate)+".json?is_preview=0&other_server=1"
			dir.Append(Function(WindowsMediaVideoItem(PlayMedia, title=str(bitrate)+'kbs, '+title, subtitle='Смотреть с другого сервера', summary=summary,thumb=pic,rating=rating, duration=duration),url=url))
	return dir
	
####################################################################################################

def PlayMedia(sender,url):	
	Log("----> URL='%s'" % (url))
	obj=JSON.ObjectFromURL(url)
	st=JSON.StringFromObject(obj)
	Log("----> OBJ='%s'" % (st))
	if obj.has_key('status'):
		if obj['status']=='ok':
			vurl=obj['url']
			title=obj['msg']
			Log("----> play from '%s'" % (vurl))
			#return Redirect(VideoItem(key=vurl, title=title ))
			return Redirect(vurl)
		else:
			title=obj['msg']
			MessageContainer("Error",title)
	else:
		return MessageContainer("Error","Some Error")
		
####################################################################################################
	
def ShowMessage(sender, title, message):
	return MessageContainer(title, message)

####################################################################################################
def Search(sender, query):
	query = re.sub (r' ', r'+', query)
	if Prefs['cyrillic'] == True:
		return Categories('Result', link='media/search.json?q=' + translit.detranslify(query).encode("utf-8"), page=1)
	else:
		return Categories('Result', link='media/search.json?q=' + query.encode("utf-8"), page=1)
	
####################################################################################################

def Login():
	global LOGGEDIN, sessionid
	if LOGGEDIN == True:
		return True
	elif not Prefs['username'] and not Prefs['password']:
		return False
	else:
		#initiate = HTTP.Request(BASE_URL+'/login/', encoding='iso-8859-1', cacheTime=1)
		values = {
			'username' : Prefs['username'],
			'password' : Prefs['password']
		}
		url = API_URL+'session.json'		
		try:
			obj = JSON.ObjectFromURL(url, values=values, encoding='utf-8', cacheTime=1)
		except:
			obj=[]
			Log("----> Someting Bad'%s'" % (values))
			LOGGEDIN = False
			return False	
		sessionid = obj['sessid']
		if len(sessionid) > 0:
			LOGGEDIN = True
			Log(" --> Login successful! %s SSID='%s'" % (LOGGEDIN,sessionid))
			return True
		else:
			LOGGEDIN = False
			Log(' --> Username/password incorrect!')
			return False
			#MessageContainer("Ошибка","Отказано в доступе")

####################################################################################################

def Thumb(url):
	if url=='':
		return Redirect(R(ICON))
	else:
		try:
			data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
			return DataObject(data, 'image/jpeg')
		except:
			return Redirect(R(ICON))
  
#################################################################################################### 

def Summary(id):
	url=API_URL +"media/details/"+str(id)+".json"
	obj=JSON.ObjectFromURL(url)
	summary=obj['media']['description']
	return summary
  
#################################################################################################### 

def About(sender):
	return MessageContainer(NAME+' (Версия ' + str(VERSION) + ')', 'Автор: Александр Титов\nwww.rozdol.com')

####################################################################################################

def CheckForUpdate():
	Log(' --> Checking for Update...')
	update = JSON.ObjectFromURL(UPDATECHECK_URL, cacheTime=1)
	if update['version'] != None and update['url'] != None:
		Log(' --> Still checking... (%s / %s)' % (update['version'],VERSION))
		if float(update['version']) > VERSION:
			Log(' --> New Version found!')
			return update['version']
		else:
			Log(' --> No New Version')
			return None

####################################################################################################

def UpdateAvailable(sender):
	return MessageContainer('Доступна новая версия', 'Новая версия плагина на\nhttp://www.rozdol.com')

####################################################################################################

def GetAccountInfo(sender):	
	
	values = {
		'act'	 : '/login/',
		'username' : Prefs['username'],
		'password' : Prefs['password']
	}
	#strvalues=JSON.StringFromObject(values)
	#Log("------> Logging... '%s'" % (BASE_URL))
	#login = HTTP.Request(BASE_URL, values=values, encoding='utf-8').content
	#Log("------> login '%s'" % (login))
	
	QRY_URL=BASE_URL+'account/'	
	body = HTTP.Request(QRY_URL, encoding='utf-8').content	
	#Log("------> BODY: '%s'" % (body))
	xp='//div[2]/div[2]/div/div[1]/div[2]/div'
	xp="id('inner-content-onecolumn')/div/div/div/div/div/div"
	xbody = XML.ElementFromString(body, isHTML=True).xpath(xp)
	Log("------> XBODY LEN'%s'" % len(xbody))
	i=0
	if len(xbody) > 0:
		for element in xbody:
			i+=1
			sss=XML.StringFromElement(element, encoding="utf8", method=None)
			balance = sss[sss.find('Баланс'):sss.find(' CAD<br>')].replace('</span>','')+' CAD'
			plan = sss[sss.find('<a href="/prices/">'):sss.find('</a><br><br><span')].replace('<a href="/prices/">','Тарифный план')
			watched = sss[sss.find('Просмотрено часов'):sss.find('мин. <br><span')].replace('</span>','')+'мин.'
			unwatched = sss[sss.find('Осталось часов'):sss.find(' <br><span class="small-text">Следующий')].replace('</span>','')+''
			username = sss[sss.find('Логин:</span> '):sss.find('<br><span')].replace('</span>','')+'.'
			Log("------> element"+str(i)+"'%s'" % (sss))
			Log("------> UNAME '%s'" % (balance))
	return MessageContainer('Счет'+username, plan+'\n'+balance+'\n'+watched+'\n'+unwatched)
#id('table-onecolumn-account')/tbody/tr
####################################################################################################

def GetViewedList(sender, page=1):	
	nextpage=page+1
	dir = MediaContainer(viewGroup='Details', httpCookies=HTTP.GetCookiesForURL(BASE_URL), title2=sender.itemTitle)
	QRY_URL=BASE_URL+'account/?page='+str(page)	
	body = HTTP.Request(QRY_URL, encoding='utf-8').content	
	#Log("------> BODY: '%s'" % (body))
	xp='//div[2]/div[2]/div/div[1]/div[2]/div'
	xp="id('table-onecolumn-account')/tbody/tr"
	xbody = XML.ElementFromString(body, isHTML=True).xpath(xp)
	Log("------> XBODY LEN'%s'" % len(xbody))
	i=0
	if len(xbody) > 0:
		for element in xbody:
			i+=1
			id=1
			thumb=''
			title=element.xpath('./td[1]/a')[0].text
			link=element.xpath('./td[1]/a')[0].get('href')
			leng=len(link)-8
			id=link[(len(link)-8):len(link)].replace('/','')
			subtitle=element.xpath('./td[2]/center')[0].text
			price=element.xpath('./td[3]/center')[0].text
			date=element.xpath('./td[4]/center')[0].text
			summary='Дата просмотра: '+date+'\nЦена: '+str(price)+'\nID='+str(id)
			rating=0
			duration=0
			dir.Append(Function(DirectoryItem(MediaInfo, title=title, subtitle=subtitle, summary=summary, thumb=Function(Thumb, url=thumb), duration=duration,rating=rating), id=id, page=1))
	dir.Append(Function(DirectoryItem(GetViewedList, title=' -> Страница '+str(nextpage),thumb=R('next.png')),  page=nextpage))
	return dir

####################################################################################################

def AddToFavorites(sender, key, sort, name, videoId=0, summary=''):
	favs = []
	if Data.Exists('favorites'):
		favs = Data.LoadObject('favorites')
		if name in favs:
			return MessageContainer('Already a favorite', 'This video is already on your list of favorites.')

	favs.append(name)
	Data.SaveObject('favorites', favs)
	return MessageContainer('Added to favorites', 'This video has been added to your favorites.')
