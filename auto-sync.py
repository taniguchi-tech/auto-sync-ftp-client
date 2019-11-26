# coding: utf-8

#####################################################################################################################
##
##	[Python2による ローカル - FTPサーバー 同期プログラム]
##
##          [author] d.taniguchi
##          [email]  info@taniguchi.tech
##          [blog]   https://blog.taniguchi.tech/archives/41
##
##
##          ローカルと、FTPサーバーそれぞれ不足しているディレクトリーやファイルを再帰的に探索し、ダウンロードや、
##          アップロードを行い補完することで、保存データが同じになるよう同期をとります。
##
##          使い方は、下の設定行に、同期対象FTPサーバーの接続先設定とディレクトリ、同期対象のローカルディレクトリ
##　　　　　を指定し、当プログラムを呼び出すだけです。
##
##          パスの指定はお尻の"/"を付けないでください。
##              ○  -  "/home/Music"
##              ×  -  "/home/Music/"
##
##
##          ただし、同一パス、同一ファイル名で、内容の異なるファイルが存在する場合無視されます。（同期済と判定）
##          ファイル名だけで判定する仕組みになっています。サイズチェックや更新日チェック等は入っていません。
##          コンソール出力で警告等も出ません。クローン数で、改良を考えます。
##
##          ローカルが空の場合、FTPサーバー上のデータのまるごとダウンロードなどにも使用できます。
##          
##          同一階層上に、同名のディレクトリやファイルが存在するために同期できない場合、コンソール出力で同期失敗
##          を出力します。
##         
##
#####################################################################################################################

#####################################################################################################################
##### 設定 ##########################################################################################################
#####################################################################################################################


# 同期対象接続先FTPサーバー設定
host = "192.168.1.1"
userId = "userId"
password = "password"
ftpDir = "/music"


# 同期対象ローカルディレクトリ設定
localDir = "/Users/User/Music"


#####################################################################################################################
##### 設定ここまで ##################################################################################################
#####################################################################################################################

import os
from ftplib import FTP

responses = []



#
# ftp転送回線のレスポンスデータを取得するcallbackです
#
def appender(data):

	# "".encode("uft-8") unicode型 -> str型
	# "".decode("utf-8") str型もしくはbyte型 -> unicode型
	# 文字化けが発生する場合
	#responses.append(data.decode("utf-8").encode("utf-8"))
	responses.append(data)



#
# FTPサーバーへCurrent Working DirectoryのLISTコマンド実行結果をオブジェクト配列で返します
#
def ftpLs():

	# TODO ファイル指定だとエラーだ。対応したい・・・
	ftp.retrlines("LIST", appender) # mlsdコマンドにしたい


	global responses
	servResponses = responses[:] # スライス記法(objectのclone)
	responses = []


	#----------------------------------------------------------------------------------------------------------------
	#
	#    [LISTコマンド 変数:s に入る値の例]
	#        drwx---r-x   6 ftp-user.jp ftpUser123     4096 Aug 27 00:07 .
	#        drwx---r-x   6 ftp-user.jp ftpUser123     4096 Aug 27 00:07 ..
	#        -rw----r--   1 ftp-user.jp ftpUser123      138 Aug 24 14:04 .htaccess
	#        -rw-r--r--   1 ftp-user.jp ftpUser123     8082 Aug 24 14:08 index.html
	#        drwxr-xr-x   4 ftp-user.jp ftpUser123     4096 Aug 27 00:08 lib
	#
	#        -rw-rw-r--    1 ftp      ftp      58353164 Sep 04 20:32 12 ＬＯＮＥＬＹ　ＷＯＭＡＮ.wav
	#        -rw-rw-r--    1 ftp      ftp      13881548 Sep 04 20:32 13 キラーストリート.wav
	#        -rw-rw-r--    1 ftp      ftp      13881548 Sep 04 20:32 13 キラー　  ;ストリート.wav
	#
	#----------------------------------------------------------------------------------------------------------------
	#----------------------------------------------------------------------------------------------------------------
	#
	#    [ftpItems]
	#		type : dir / file 
	#		name : dir name / file name 
	#
	#----------------------------------------------------------------------------------------------------------------
	ftpItems = []

	for s in servResponses:

		cnt = 0
		startPoint = 0
		itemType = ""

		for currentPoint in range(0, len(s) - 1, 1):

			#------------------------------------------------------------------------------------------------
			#
			#	FTPプロトコル LISTコマンドのレスポンスのうち、最初のmodとnameのみを抽出する処理
			#	複数スペースを半角スペース1文字に置換してsplitするという発想は、ファイル名にスペース、複数スペースが
			#	使用されていた場合、対応不能となるので注意
			#
			#			cnt
			#		+	[0] : [mod] (1文字目のみ)
			#			[1] : [file count]
			#			[2] : [user]
			# 			[3] : [group]
			#			[4] : [capacity]
			#			[5] : [month]
			#			[6] : [day]
			#			[7] : [time]
			#		+	[8] : [dir/file name]
			#
			#------------------------------------------------------------------------------------------------

			if s[currentPoint] != " " and s[currentPoint + 1] == " ":
				if cnt == 0:
					mod = s[startPoint : currentPoint + 1]  # 1文字のパラメーターの場合を考慮しない
					if "d" == mod[0]:
						itemType = "dir"
					elif "-" == mod[0]:
						itemType = "file"
				cnt += 1
			elif (cnt == 0 or cnt == 8) and s[currentPoint] == " " and s[currentPoint + 1] != " ":
				startPoint = currentPoint + 1
				if cnt == 8:
					break

		itemName = s[startPoint:len(s)]

		if "." != itemName and ".." != itemName:
			ftpItems.append({"type" : itemType, "name" : itemName})

	return ftpItems



#
# 接続先FTPサーバーに同名のファイル、もしくはディレクトリがある場合、Trueを返します
#
def isExistsItem(ftpItems, itemName):
	for ftpItem in ftpItems:
		if ftpItem["name"] == itemName:
			return True
	return False



#
# 接続先FTPサーバーに同名のディレクトリがある場合、Trueを返します
#
def isExistsItemAndIsDirectory(ftpItems, itemName):
	for ftpItem in ftpItems:
		if ftpItem["name"] == itemName:
			return ftpItem["type"] == "dir"
	return False


#
# ディレクトリとファイルを同期する再帰メソッドです
#
def sync(localPath, ftpPath):


	ftp.cwd(ftpPath)
	os.chdir(localPath)

	ftpItems = ftpLs()
	localItems = os.listdir(".")

	# ディレクトリを同期
	for ftpItem in ftpItems:
		if ftpItem["type"] == "dir" and ftpItem["name"] not in localItems:
			try:
				os.makedirs(ftpItem["name"])
			except:
				print("ローカル上にディレクトリを作成するのに失敗しました。[" + localPath + "/" + ftpItem["name"] + "]")

	for localItem in localItems:
		if os.path.isdir(localItem) and not isExistsItem(ftpItems, localItem):
			try:
				ftp.mkd(localItem)
			except:
				print("FTPサーバー上にディレクトリを作成するのに失敗しました。[" + ftpPath + "/" + localItem + "]")


	# ファイルを同期
	for ftpItem in ftpItems:
		if ftpItem["type"] == "file" and ftpItem["name"] not in localItems:
			saveFileName = localPath + "/" + ftpItem["name"]
			print("Donwload Now: " + saveFileName)
			try:
				ftp.retrbinary("RETR " + ftpItem["name"], open(saveFileName, "wb").write)
			except:
				print("ローカル上にファイルを作成するのに失敗しました。[" + saveFileName + "]")

	for localItem in localItems:
		if not os.path.isdir(localItem) and not isExistsItem(ftpItems, localItem):
			print("Upload Now: " + localPath + "/" + localItem)
			try:
				ftp.storbinary("STOR " + ftpPath + "/" + localItem, open(localPath + "/" + localItem, "rb"))
			except:
				print("FTPサーバー上にファイルを作成するのに失敗しました。[" + ftpPath + "/" + localItem + "]")


	ftpItems = ftpLs()
	localItems = os.listdir(".")

	# ディレクトリと同名ファイルチェック・再帰
	for ftpItem in ftpItems:
		if ftpItem["type"] == dir and not os.path.isdir(ftpItem["name"]):
			print("FTPサーバー上にディレクトリ名と同名のファイルが存在したため、同期をスキップしました。 [local:" + localPath + "/" + ftpItem["name"] + "]")

	for localItem in localItems:
		if os.path.isdir(localPath + "/" + localItem):
			if isExistsItemAndIsDirectory(ftpItems, localItem):
				sync(localPath + "/" + localItem, ftpPath + "/" + localItem)
			else:
				print("ローカル上にディレクトリ名と同名のファイルが存在したため、同期をスキップしました。[FTP:" + ftpPath + "/" + localItem + "]")


	#print("同期完了:" + localPath)


#####################################################################################################################

print("接続中")
ftp = FTP(
	host,
	userId,
	passwd = password
)
ftp.sendcmd('OPTS UTF8 ON')
print("接続完了")

print("同期処理を開始します")
sync(localDir, ftpDir)

ftp.quit()

print("同期処理が完了しました")

#####################################################################################################################
