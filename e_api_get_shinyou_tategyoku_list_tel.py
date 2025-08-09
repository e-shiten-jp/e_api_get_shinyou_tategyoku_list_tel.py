# -*- coding: utf-8 -*-
# Copyright (c) 2021 Tachibana Securities Co., Ltd. All rights reserved.

# 2021.07.08,   yo.
# 2022.10.20 reviced,   yo.
# 2025.07.27 reviced,   yo.
#
# 立花証券ｅ支店ＡＰＩ利用のサンプルコード
#
# 動作確認
# Python 3.11.2 / debian12
# API v4r7
#
# 機能: 信用建玉一覧の取得
#
# 設定項目
# 必要設定項目
# 銘柄コード  '':省略時全銘柄取得
#
#
# 利用方法: 
# 事前に「e_api_login_tel.py」を実行して、
# 仮想URL（1日券）等を取得しておいてください。
# 「e_api_login_tel.py」と同じディレクトリで実行してください。
#
#
# == ご注意: ========================================
#   本番環境にに接続した場合、実際に市場に注文が出ます。
#   市場で約定した場合取り消せません。
# ==================================================
#

import urllib3
import datetime
import json
import time


#--- 共通コード ------------------------------------------------------

# request項目を保存するクラス。配列として使う。
class class_req :
    def __init__(self) :
        self.str_key = ''
        self.str_value = ''
        
    def add_data(self, work_key, work_value) :
        self.str_key = func_check_json_dquat(work_key)
        self.str_value = func_check_json_dquat(work_value)


# 口座属性クラス
class class_def_account_property:
    def __init__(self):
        self.sUserId = ''           # userid
        self.sPassword = ''         # password
        self.sSecondPassword = ''   # 第2パスワード
        self.sUrl = ''              # 接続先URL
        self.sJsonOfmt = 5          # 返り値の表示形式指定
        
# ログイン属性クラス
class class_def_login_property:
    def __init__(self):
        self.p_no = 0                       # 累積p_no
        self.sJsonOfmt = ''                 # 返り値の表示形式指定
        self.sResultCode = ''               # 結果コード
        self.sResultText = ''               # 結果テキスト
        self.sZyoutoekiKazeiC = ''          # 譲渡益課税区分  1：特定  3：一般  5：NISA
        self.sSecondPasswordOmit = ''       # 暗証番号省略有無Ｃ  22.第二パスワード  APIでは第2暗証番号を省略できない。 関連資料:「立花証券・e支店・API、インターフェース概要」の「3-2.ログイン、ログアウト」参照
        self.sLastLoginDate = ''            # 最終ログイン日時
        self.sSogoKouzaKubun = ''           # 総合口座開設区分  0：未開設  1：開設
        self.sHogoAdukariKouzaKubun = ''    # 保護預り口座開設区分  0：未開設  1：開設
        self.sFurikaeKouzaKubun = ''        # 振替決済口座開設区分  0：未開設  1：開設
        self.sGaikokuKouzaKubun = ''        # 外国口座開設区分  0：未開設  1：開設
        self.sMRFKouzaKubun = ''            # ＭＲＦ口座開設区分  0：未開設  1：開設
        self.sTokuteiKouzaKubunGenbutu = '' # 特定口座区分現物  0：一般  1：特定源泉徴収なし  2：特定源泉徴収あり
        self.sTokuteiKouzaKubunSinyou = ''  # 特定口座区分信用  0：一般  1：特定源泉徴収なし  2：特定源泉徴収あり
        self.sTokuteiKouzaKubunTousin = ''  # 特定口座区分投信  0：一般  1：特定源泉徴収なし  2：特定源泉徴収あり
        self.sTokuteiHaitouKouzaKubun = ''  # 配当特定口座区分  0：未開設  1：開設
        self.sTokuteiKanriKouzaKubun = ''   # 特定管理口座開設区分  0：未開設  1：開設
        self.sSinyouKouzaKubun = ''         # 信用取引口座開設区分  0：未開設  1：開設
        self.sSakopKouzaKubun = ''          # 先物ＯＰ口座開設区分  0：未開設  1：開設
        self.sMMFKouzaKubun = ''            # ＭＭＦ口座開設区分  0：未開設  1：開設
        self.sTyukokufKouzaKubun = ''       # 中国Ｆ口座開設区分  0：未開設  1：開設
        self.sKawaseKouzaKubun = ''         # 為替保証金口座開設区分  0：未開設  1：開設
        self.sHikazeiKouzaKubun = ''        # 非課税口座開設区分  0：未開設  1：開設  ※ＮＩＳＡ口座の開設有無を示す。
        self.sKinsyouhouMidokuFlg = ''      # 金商法交付書面未読フラグ  1：未読（標準Ｗｅｂを起動し書面確認実行必須）  0：既読  ※未読の場合、ｅ支店・ＡＰＩは利用不可のため    仮想ＵＲＬは発行されず""を設定。  ※既読の場合、ｅ支店・ＡＰＩは利用可能となり    仮想ＵＲＬを発行し設定。  
        self.sUrlRequest = ''               # 仮想URL（REQUEST)  業務機能    （REQUEST I/F）仮想URL
        self.sUrlMaster = ''                # 仮想URL（MASTER)  マスタ機能  （REQUEST I/F）仮想URL
        self.sUrlPrice = ''                 # 仮想URL（PRICE)  時価情報機能（REQUEST I/F）仮想URL
        self.sUrlEvent = ''                 # 仮想URL（EVENT)  注文約定通知（EVENT I/F）仮想URL
        self.sUrlEventWebSocket = ''        # 仮想URL（EVENT-WebSocket)  注文約定通知（EVENT I/F WebSocket版）仮想URL
        self.sUpdateInformWebDocument = ''  # 交付書面更新予定日  標準Ｗｅｂの交付書面更新予定日決定後、該当日付を設定。  【注意】参照
        self.sUpdateInformAPISpecFunction = ''  # ｅ支店・ＡＰＩリリース予定日  ｅ支店・ＡＰＩリリース予定日決定後、該当日付を設定。  【注意】参照

        

# 機能: システム時刻を"p_sd_date"の書式の文字列で返す。
# 返値: "p_sd_date"の書式の文字列
# 引数1: システム時刻
# 備考:  "p_sd_date"の書式：YYYY.MM.DD-hh:mm:ss.sss
def func_p_sd_date(int_systime):
    str_psddate = ''
    str_psddate = str_psddate + str(int_systime.year) 
    str_psddate = str_psddate + '.' + ('00' + str(int_systime.month))[-2:]
    str_psddate = str_psddate + '.' + ('00' + str(int_systime.day))[-2:]
    str_psddate = str_psddate + '-' + ('00' + str(int_systime.hour))[-2:]
    str_psddate = str_psddate + ':' + ('00' + str(int_systime.minute))[-2:]
    str_psddate = str_psddate + ':' + ('00' + str(int_systime.second))[-2:]
    str_psddate = str_psddate + '.' + (('000000' + str(int_systime.microsecond))[-6:])[:3]
    return str_psddate


# JSONの値の前後にダブルクオーテーションが無い場合付ける。
def func_check_json_dquat(str_value) :
    if len(str_value) == 0 :
        str_value = '""'
        
    if not str_value[:1] == '"' :
        str_value = '"' + str_value
        
    if not str_value[-1:] == '"' :
        str_value = str_value + '"'
        
    return str_value
    
    
# 受けたテキストの１文字目と最終文字の「"」を削除
# 引数：string
# 返り値：string
def func_strip_dquot(text):
    if len(text) > 0:
        if text[0:1] == '"' :
            text = text[1:]
            
    if len(text) > 0:
        if text[-1] == '\n':
            text = text[0:-1]
        
    if len(text) > 0:
        if text[-1:] == '"':
            text = text[0:-1]
        
    return text
    


# 機能: URLエンコード文字の変換
# 引数1: 文字列
# 返値: URLエンコード文字に変換した文字列
# 
# URLに「#」「+」「/」「:」「=」などの記号を利用した場合エラーとなる場合がある。
# APIへの入力文字列（特にパスワードで記号を利用している場合）で注意が必要。
#   '#' →   '%23'
#   '+' →   '%2B'
#   '/' →   '%2F'
#   ':' →   '%3A'
#   '=' →   '%3D'
def func_replace_urlecnode( str_input ):
    str_encode = ''
    str_replace = ''
    
    for i in range(len(str_input)):
        str_char = str_input[i:i+1]

        if str_char == ' ' :
            str_replace = '%20'       #「 」 → 「%20」 半角空白
        elif str_char == '!' :
            str_replace = '%21'       #「!」 → 「%21」
        elif str_char == '"' :
            str_replace = '%22'       #「"」 → 「%22」
        elif str_char == '#' :
            str_replace = '%23'       #「#」 → 「%23」
        elif str_char == '$' :
            str_replace = '%24'       #「$」 → 「%24」
        elif str_char == '%' :
            str_replace = '%25'       #「%」 → 「%25」
        elif str_char == '&' :
            str_replace = '%26'       #「&」 → 「%26」
        elif str_char == "'" :
            str_replace = '%27'       #「'」 → 「%27」
        elif str_char == '(' :
            str_replace = '%28'       #「(」 → 「%28」
        elif str_char == ')' :
            str_replace = '%29'       #「)」 → 「%29」
        elif str_char == '*' :
            str_replace = '%2A'       #「*」 → 「%2A」
        elif str_char == '+' :
            str_replace = '%2B'       #「+」 → 「%2B」
        elif str_char == ',' :
            str_replace = '%2C'       #「,」 → 「%2C」
        elif str_char == '/' :
            str_replace = '%2F'       #「/」 → 「%2F」
        elif str_char == ':' :
            str_replace = '%3A'       #「:」 → 「%3A」
        elif str_char == ';' :
            str_replace = '%3B'       #「;」 → 「%3B」
        elif str_char == '<' :
            str_replace = '%3C'       #「<」 → 「%3C」
        elif str_char == '=' :
            str_replace = '%3D'       #「=」 → 「%3D」
        elif str_char == '>' :
            str_replace = '%3E'       #「>」 → 「%3E」
        elif str_char == '?' :
            str_replace = '%3F'       #「?」 → 「%3F」
        elif str_char == '@' :
            str_replace = '%40'       #「@」 → 「%40」
        elif str_char == '[' :
            str_replace = '%5B'       #「[」 → 「%5B」
        elif str_char == ']' :
            str_replace = '%5D'       #「]」 → 「%5D」
        elif str_char == '^' :
            str_replace = '%5E'       #「^」 → 「%5E」
        elif str_char == '`' :
            str_replace = '%60'       #「`」 → 「%60」
        elif str_char == '{' :
            str_replace = '%7B'       #「{」 → 「%7B」
        elif str_char == '|' :
            str_replace = '%7C'       #「|」 → 「%7C」
        elif str_char == '}' :
            str_replace = '%7D'       #「}」 → 「%7D」
        elif str_char == '~' :
            str_replace = '%7E'       #「~」 → 「%7E」
        else :
            str_replace = str_char
        str_encode = str_encode + str_replace        
    return str_encode


# 機能： ファイルから文字情報を読み込み、その文字列を返す。
# 戻り値： 文字列
# 第１引数： ファイル名
# 備考： json形式のファイルを想定。
def func_read_from_file(str_fname):
    str_read = ''
    try:
        with open(str_fname, 'r', encoding = 'utf_8') as fin:
            while True:
                line = fin.readline()
                if not len(line):
                    break
                str_read = str_read + line
        return str_read
    except IOError as e:
        print('ファイルを読み込めません!!! ファイル名：',str_fname)
        print(type(e))


# 機能: ファイルに書き込む
# 引数1: 出力ファイル名
# 引数2: 出力するデータ
# 備考:
def func_write_to_file(str_fname_output, str_data):
    try:
        with open(str_fname_output, 'w', encoding = 'utf-8') as fout:
            fout.write(str_data)
    except IOError as e:
        print('ファイルに書き込めません!!!  ファイル名：',str_fname_output)
        print(type(e))


# 機能: class_req型データをjson形式の文字列に変換する。
# 返値: json形式の文字
# 第１引数： class_req型データ
def func_make_json_format(work_class_req):
    work_key = ''
    work_value = ''
    str_json_data =  '{\n\t'
    for i in range(len(work_class_req)) :
        work_key = func_strip_dquot(work_class_req[i].str_key)
        if len(work_key) > 0:
            if work_key[:1] == 'a' :
                work_value = work_class_req[i].str_value
                str_json_data = str_json_data + work_class_req[i].str_key \
                                    + ':' + func_strip_dquot(work_value) \
                                    + ',\n\t'
            else :
                work_value = func_check_json_dquat(work_class_req[i].str_value)
                str_json_data = str_json_data + func_check_json_dquat(work_class_req[i].str_key) \
                                    + ':' + work_value \
                                    + ',\n\t'
    str_json_data = str_json_data[:-3] + '\n}'
    return str_json_data


# 機能： API問合せ文字列を作成し返す。
# 戻り値： api問合せのurl文字列
# 第１引数： ログインは、Trueをセット。それ以外はFalseをセット。
# 第2引数： ログインは、APIのurlをセット。それ以外はログインで返された仮想url（'sUrlRequest'等）の値をセット。
# 第３引数： 要求項目のデータセット。クラスの配列として受取る。
def func_make_url_request(auth_flg, \
                          url_target, \
                          work_class_req) :
    str_url = url_target
    if auth_flg == True :   # ログインの場合
        str_url = str_url + 'auth/'
    str_url = str_url + '?'
    str_url = str_url + func_make_json_format(work_class_req)
    return str_url


# 機能: API問合せ。通常のrequest,price用。
# 返値: API応答（辞書型）
# 第１引数： URL文字列。
# 備考: APIに接続し、requestの文字列を送信し、応答データを辞書型で返す。
#       master取得は専用の func_api_req_muster を利用する。
def func_api_req(str_url): 
    print('送信文字列＝')
    print(str_url)  # 送信する文字列

    # APIに接続
    http = urllib3.PoolManager()
    req = http.request('GET', str_url)
    print("req.status= ", req.status )

    # 取得したデータを、json.loadsを利用できるようにstr型に変換する。日本語はshift-jis。
    bytes_reqdata = req.data
    str_shiftjis = bytes_reqdata.decode("shift-jis", errors="ignore")

    print('返信文字列＝')
    print(str_shiftjis)

    # JSON形式の文字列を辞書型で取り出す
    json_req = json.loads(str_shiftjis)

    return json_req


# 機能： アカウント情報をファイルから取得する
# 引数1: 口座情報を保存したファイル名
# 引数2: 口座情報（class_def_account_property型）データ
def func_get_acconut_info(fname, class_account_property):
    str_account_info = func_read_from_file(fname)
    # JSON形式の文字列を辞書型で取り出す
    json_account_info = json.loads(str_account_info)

    class_account_property.sUserId = json_account_info.get('sUserId')
    class_account_property.sPassword = json_account_info.get('sPassword')
    class_account_property.sSecondPassword = json_account_info.get('sSecondPassword')
    class_account_property.sUrl = json_account_info.get('sUrl')

    # 返り値の表示形式指定
    class_account_property.sJsonOfmt = json_account_info.get('sJsonOfmt')
    # "5"は "1"（1ビット目ON）と”4”（3ビット目ON）の指定となり
    # ブラウザで見や易い形式」且つ「引数項目名称」で応答を返す値指定


# 機能： ログイン情報をファイルから取得する
# 引数1: ログイン情報を保存したファイル名（fname_login_response = "e_api_login_response.txt"）
# 引数2: ログインデータ型（class_def_login_property型）
def func_get_login_info(str_fname, class_login_property):
    str_login_respons = func_read_from_file(str_fname)
    dic_login_respons = json.loads(str_login_respons)

    class_login_property.sResultCode = dic_login_respons.get('sResultCode')                 # 結果コード
    class_login_property.sResultText = dic_login_respons.get('sResultText')                 # 結果テキスト
    class_login_property.sZyoutoekiKazeiC = dic_login_respons.get('sZyoutoekiKazeiC')       # 譲渡益課税区分  1：特定  3：一般  5：NISA
    class_login_property.sSecondPasswordOmit = dic_login_respons.get('sSecondPasswordOmit')     # 暗証番号省略有無Ｃ
    class_login_property.sLastLoginDate = dic_login_respons.get('sLastLoginDate')               # 最終ログイン日時
    class_login_property.sSogoKouzaKubun = dic_login_respons.get('sSogoKouzaKubun')             # 総合口座開設区分  0：未開設  1：開設
    class_login_property.sHogoAdukariKouzaKubun = dic_login_respons.get('sHogoAdukariKouzaKubun')       # 保護預り口座開設区分  0：未開設  1：開設
    class_login_property.sFurikaeKouzaKubun = dic_login_respons.get('sFurikaeKouzaKubun')               # 振替決済口座開設区分  0：未開設  1：開設
    class_login_property.sGaikokuKouzaKubun = dic_login_respons.get('sGaikokuKouzaKubun')               # 外国口座開設区分  0：未開設  1：開設
    class_login_property.sMRFKouzaKubun = dic_login_respons.get('sMRFKouzaKubun')                       # ＭＲＦ口座開設区分  0：未開設  1：開設
    class_login_property.sTokuteiKouzaKubunGenbutu = dic_login_respons.get('sTokuteiKouzaKubunGenbutu') # 特定口座区分現物  0：一般  1：特定源泉徴収なし  2：特定源泉徴収あり
    class_login_property.sTokuteiKouzaKubunSinyou = dic_login_respons.get('sTokuteiKouzaKubunSinyou')   # 特定口座区分信用  0：一般  1：特定源泉徴収なし  2：特定源泉徴収あり
    class_login_property.sTokuteiKouzaKubunTousin = dic_login_respons.get('sTokuteiKouzaKubunTousin')   # 特定口座区分投信  0：一般  1：特定源泉徴収なし  2：特定源泉徴収あり
    class_login_property.sTokuteiHaitouKouzaKubun = dic_login_respons.get('sTokuteiHaitouKouzaKubun')   # 配当特定口座区分  0：未開設  1：開設
    class_login_property.sTokuteiKanriKouzaKubun = dic_login_respons.get('sTokuteiKanriKouzaKubun')     # 特定管理口座開設区分  0：未開設  1：開設
    class_login_property.sSinyouKouzaKubun = dic_login_respons.get('sSinyouKouzaKubun')         # 信用取引口座開設区分  0：未開設  1：開設
    class_login_property.sSinyouKouzaKubun = dic_login_respons.get('sSinyouKouzaKubun')         # 信用取引口座開設区分  0：未開設  1：開設
    class_login_property.sSakopKouzaKubun = dic_login_respons.get('sSakopKouzaKubun')           # 先物ＯＰ口座開設区分  0：未開設  1：開設
    class_login_property.sMMFKouzaKubun = dic_login_respons.get('sMMFKouzaKubun')               # ＭＭＦ口座開設区分  0：未開設  1：開設
    class_login_property.sTyukokufKouzaKubun = dic_login_respons.get('sTyukokufKouzaKubun')     # 中国Ｆ口座開設区分  0：未開設  1：開設
    class_login_property.sKawaseKouzaKubun = dic_login_respons.get('sKawaseKouzaKubun')         # 為替保証金口座開設区分  0：未開設  1：開設
    class_login_property.sHikazeiKouzaKubun = dic_login_respons.get('sHikazeiKouzaKubun')       # 非課税口座開設区分  0：未開設  1：開設  ※ＮＩＳＡ口座の開設有無を示す。
    class_login_property.sKinsyouhouMidokuFlg = dic_login_respons.get('sKinsyouhouMidokuFlg')   # 金商法交付書面未読フラグ  1：未読（標準Ｗｅｂを起動し書面確認実行必須）  0：既読  ※未読の場合、ｅ支店・ＡＰＩは利用不可のため    仮想ＵＲＬは発行されず""を設定。  ※既読の場合、ｅ支店・ＡＰＩは利用可能となり    仮想ＵＲＬを発行し設定。  
    class_login_property.sUrlRequest = dic_login_respons.get('sUrlRequest')     # 仮想URL（REQUEST)  業務機能    （REQUEST I/F）仮想URL
    class_login_property.sUrlMaster = dic_login_respons.get('sUrlMaster')       # 仮想URL（MASTER)  マスタ機能  （REQUEST I/F）仮想URL
    class_login_property.sUrlPrice = dic_login_respons.get('sUrlPrice')         # 仮想URL（PRICE)  時価情報機能（REQUEST I/F）仮想URL
    class_login_property.sUrlEvent = dic_login_respons.get('sUrlEvent')         # 仮想URL（EVENT)  注文約定通知（EVENT I/F）仮想URL
    class_login_property.sUrlEventWebSocket = dic_login_respons.get('sUrlEventWebSocket')    # 仮想URL（EVENT-WebSocket)  注文約定通知（EVENT I/F WebSocket版）仮想URL
    class_login_property.sUpdateInformWebDocument = dic_login_respons.get('sUpdateInformWebDocument')    # 交付書面更新予定日  標準Ｗｅｂの交付書面更新予定日決定後、該当日付を設定。  【注意】参照
    class_login_property.sUpdateInformAPISpecFunction = dic_login_respons.get('sUpdateInformAPISpecFunction')    # ｅ支店・ＡＰＩリリース予定日  ｅ支店・ＡＰＩリリース予定日決定後、該当日付を設定。  【注意】参照
    

# 機能： p_noをファイルから取得する
# 引数1: p_noを保存したファイル名（fname_info_p_no = "e_api_info_p_no.txt"）
# 引数2: login情報（class_def_login_property型）データ
def func_get_p_no(fname, class_login_property):
    str_p_no_info = func_read_from_file(fname)
    # JSON形式の文字列を辞書型で取り出す
    json_p_no_info = json.loads(str_p_no_info)
    class_login_property.p_no = int(json_p_no_info.get('p_no'))
        
    
# 機能: p_noを保存するためのjson形式のテキストデータを作成します。
# 引数1: p_noを保存するファイル名（fname_info_p_no = "e_api_info_p_no.txt"）
# 引数2: 保存するp_no
# 備考:
def func_save_p_no(str_fname_output, int_p_no):
    # "p_no"を保存する。
    str_info_p_no = '{\n'
    str_info_p_no = str_info_p_no + '\t' + '"p_no":"' + str(int_p_no) + '"\n'
    str_info_p_no = str_info_p_no + '}\n'
    func_write_to_file(str_fname_output, str_info_p_no)
    print('現在の"p_no"を保存しました。 p_no =', int_p_no)            
    print('ファイル名:', str_fname_output)

#--- 以上 共通コード -------------------------------------------------




# 参考資料（必ず最新の資料を参照してください。）
#マニュアル
#「立花証券・ｅ支店・ＡＰＩ（v4r2）、REQUEST I/F、機能毎引数項目仕様」
# (api_request_if_clumn_v4r2.pdf)
# p10/46 No.9 CLMShinyouTategyokuList を参照してください。
#
#   9 CLMShinyouTategyokuList
#  1	sCLMID	メッセージＩＤ	char*	I/O	'CLMShinyouTategyokuList'
#  2	sIssueCode	銘柄コード	char[12]	I/O	銘柄コード（6501 等）
#  3	sResultCode	結果コード	char[9]	O	業務処理．エラーコード 0：正常、5桁数字：「結果テキスト」に対応するエラーコード
#  4	sResultText	結果テキスト	char[512]	O	ShiftJis  「結果コード」に対応するテキスト
#  5	sWarningCode	警告コード	char[9]	O	業務処理．ワーニングコード 0：正常、5桁数字：「警告テキスト」に対応するワーニングコード
#  6	sWarningText	警告テキスト	char[512]	O	ShiftJis  「警告コード」に対応するテキスト
#  7	sUritateDaikin	売建代金合計	char[9]	O	照会機能仕様書 ２－２．（３）、（１）残高 No.2。
#							0～9999999999999999、左詰め、マイナスの場合なし
#  8	sKaitateDaikin	買建代金合計	char[16]	O	照会機能仕様書 ２－２．（３）、（１）残高 No.1。
#								0～9999999999999999、左詰め、マイナスの場合なし
#  9	sTotalDaikin	総代金合計	char[16]	O	照会機能仕様書 ２－２．（３）、（１）残高 No.3。
#								0～9999999999999999、左詰め、マイナスの場合なし
# 10	sHyoukaSonekiGoukeiUridate	評価損益合計_売建	char[16]    O	照会機能仕様書 ２－２．（３）、（１）残高 No.7。
#									-999999999999999～9999999999999999、左詰め、マイナスの場合あり
# 11	sHyoukaSonekiGoukeiKaidate	評価損益合計_買建	char[16]    O	照会機能仕様書 ２－２．（３）、（１）残高 No.8。
#									-999999999999999～9999999999999999、左詰め、マイナスの場合あり
# 12	sTotalHyoukaSonekiGoukei	総評価損益合計	char[16]    O	照会機能仕様書 ２－２．（３）、（１）残高 No.6。
#									-999999999999999～9999999999999999、左詰め、マイナスの場合あり
# 13	sTokuteiHyoukaSonekiGoukei	特定口座残高評価損益合計    char[16]    O	照会機能仕様書 ２－２．（３）、（１）残高 No.4。
#									        -999999999999999～9999999999999999、左詰め、マイナスの場合あり
# 14	sIppanHyoukaSonekiGoukei	一般口座残高評価損益合計	char[16]    O	照会機能仕様書 ２－２．（３）、（１）残高 No.5。
#									        -999999999999999～9999999999999999、左詰め、マイナスの場合あり
# 15	aShinyouTategyokuList	信用建玉リスト	char[17]	O	以下レコードを配列で設定
# 16-1	sOrderWarningCode	警告コード	char[9]	O	業務処理．ワーニングコード 
#										0：正常、
#										5桁数字：「警告テキスト」に対応するワーニングコード
# 17-2	sOrderWarningText	警告テキスト	char[512]	O	ShiftJis  「警告コード」に対応するテキスト
# 18-3	sOrderTategyokuNumber	建玉番号	char[15]	O	-
# 19-4	sOrderIssueCode	銘柄コード	char[12]	O	-
# 20-5	sOrderSizyouC	市場	char[2]	O	00：東証
# 21-6	sOrderBaibaiKubun	売買区分	char[1]	O	1：売
#   					3：買
#   					5：現渡
#   					7：現引
# 22-7	sOrderBensaiKubun	弁済区分	char[2]	O	00：なし
#   					26：制度信用6ヶ月
#   					29：制度信用無期限
#   					36：一般信用6ヶ月
#   					39：一般信用無期限
# 23-8	sOrderZyoutoekiKazeiC	譲渡益課税区分	char[1]	O	1：特定
#   					3：一般
#   					5：NISA
# 24-9	sOrderTategyokuSuryou	建株数	char[13]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.10。
#								0～9999999999999、左詰め、マイナスの場合なし
# 25-10	sOrderTategyokuTanka	建単価	char[14]	O	0.0000～999999999.9999、左詰め、マイナスの場合なし、小数点以下桁数切詰
# 26-11	sOrderHyoukaTanka	評価単価	char[14]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.13。
#								0.0000～999999999.9999、左詰め、マイナスの場合なし、小数点以下桁数切詰
# 27-12	sOrderGaisanHyoukaSoneki	評価損益	char[16]    O   照会機能仕様書 ２－２．（３）、（２）一覧 No.14。
#								-999999999999999～9999999999999999、左詰め、マイナスの場合あり
# 28-13	sOrderGaisanHyoukaSonekiRitu	評価損益率   char[13]    O   照会機能仕様書 ２－２．（３）、（２）一覧 No.22。
#								    -999999999.99～9999999999.99、左詰め、マイナスの場合あり、小数点以下桁数切詰めなし
# 29-14	sTategyokuDaikin	建玉代金	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.23。
#								0～9999999999999999、左詰め、マイナスの場合なし
# 30-15	sOrderTateTesuryou	建手数料	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.15。
#								0～9999999999999999、左詰め、マイナスの場合なし
# 31-16	sOrderZyunHibu	順日歩	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.16。
#							0～9999999999999999、左詰め、マイナスの場合なし
# 32-17	sOrderGyakuhibu	逆日歩	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.17。
#							0～9999999999999999、左詰め、マイナスの場合なし
# 33-18	sOrderKakikaeryou	書換料	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.18。
#								0～9999999999999999、左詰め、マイナスの場合なし
# 34-19	sOrderKanrihi	管理費	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.19。
#							0～9999999999999999、左詰め、マイナスの場合なし
# 35-20	sOrderKasikaburyou	貸株料	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.20。
#								0～9999999999999999、左詰め、マイナスの場合なし
# 36-21	sOrderSonota	その他	char[16]	O	照会機能仕様書 ２－２．（３）、（２）一覧 No.21。
#							0～9999999999999999、左詰め、マイナスの場合なし
# 37-22	sOrderTategyokuDay	建日	char[8]	O	YYYYMMDD,00000000
# 38-23	sOrderTategyokuKizituDay	建玉期日日	char[8]	O	YYYYMMDD、無期限の場合は 00000000
# 39-24	sTategyokuSuryou	建玉数量	char[13]	O	0～9999999999999、左詰め、マイナスの場合なし
# 40-25	sOrderYakuzyouHensaiKabusu	約定返済株数	char[13]	O	0～9999999999999、左詰め、マイナスの場合なし
# 41-26	sOrderGenbikiGenwatasiKabusu	現引現渡株数	char[13]	O	0～9999999999999、左詰め、マイナスの場合なし
# 42-27	sOrderOrderSuryou	注文中数量	char[13]    O	0～9999999999999、左詰め、マイナスの場合なし
# 43-28	sOrderHensaiKanouSuryou	返済可能数量	char[13]    O	照会機能仕様書 ２－２．（３）、（２）一覧 No.31。
#								0～9999999999999、左詰め、マイナスの場合なし
# 44-29	sSyuzituOwarine	前日終値	    char[14]    O   照会機能仕様書 ２－２．（３）、（２）一覧 No.24。
#						    0.0000～999999999.9999、左詰め、マイナスの場合なし、小数点以下桁数切詰
# 45-30	sZenzituHi	前日比	    char[14]    O   照会機能仕様書 ２－２．（３）、（２）一覧 No.25。
#						    -9999999.9999～99999999.9999、左詰め、マイナスの場合あり、小数点以下桁数切詰めなし
# 46-31	sZenzituHiPer	前日比()      char[7]	O   照会機能仕様書 ２－２．（３）、（２）一覧 No.26。
#						    -999.99～999.99、左詰め、マイナスの場合あり、小数点以下桁数切詰めなし
# 47-32	sUpDownFlag	騰落率Flag     char[2]	O   照会機能仕様書 ２－２．（３）、（２）一覧 No.27 11段階のFlag
#   					            01：+5.01  以上
#   					            02：+3.01  ～+5.00
#   					            03：+2.01  ～+3.00
#   					            04：+1.01  ～+2.00
#   					            05：+0.01  ～+1.00
#   					            06：0 変化なし
#   					            07：-0.01  ～-1.00
#   					            08：-1.01  ～-2.00
#   					            09：-2.01  ～-3.00
#   					            10：-3.01  ～-5.00
#   					            11：-5.01  以下




# --------------------------
# 機能: 信用建玉一覧取得
# 返値: API応答（辞書型）
# 引数1: p_no
# 引数2: 銘柄コード（6501等、'':省略時全銘柄取得）
# 引数3: class_login_property（request通番）, 口座属性クラス
# 備考:
#       銘柄コードは省略可。
def func_get_shinyou_tategyoku_list(int_p_no,
                                str_sIssueCode,
                                class_login_property):

    req_item = [class_req()]
    str_p_sd_date = func_p_sd_date(datetime.datetime.now())     # システム時刻を所定の書式で取得

    str_key = '"p_no"'
    str_value = func_check_json_dquat(str(int_p_no))
    #req_item.append(class_req())
    req_item[-1].add_data(str_key, str_value)

    str_key = '"p_sd_date"'
    str_value = str_p_sd_date
    req_item.append(class_req())
    req_item[-1].add_data(str_key, str_value)

    # コマンド
    str_key = '"sCLMID"'
    str_value = 'CLMShinyouTategyokuList'  # 信用建玉一覧取得
    req_item.append(class_req())
    req_item[-1].add_data(str_key, str_value)
    
    # 銘柄コード
    str_key = '"sIssueCode"'
    str_value = str_sIssueCode      # 銘柄コード（6501等、'':省略時全銘柄取得）。
    req_item.append(class_req())
    req_item[-1].add_data(str_key, str_value)
    
    # 返り値の表示形式指定
    str_key = '"sJsonOfmt"'
    str_value = class_login_property.sJsonOfmt    # "5"は "1"（ビット目ＯＮ）と”4”（ビット目ＯＮ）の指定となり「ブラウザで見や易い形式」且つ「引数項目名称」で応答を返す値指定
    req_item.append(class_req())
    req_item[-1].add_data(str_key, str_value)

    # URL文字列の作成
    str_url = func_make_url_request(False, \
                                     class_login_property.sUrlRequest, \
                                     req_item)

    json_return = func_api_req(str_url)

    return json_return





    
# ======================================================================================================
# ==== プログラム始点 =================================================================================
# ======================================================================================================
# 機能: 信用建玉一覧取得を行ないます。
#
# 必要設定項目
# 銘柄コード  '':省略時全銘柄取得
#
if __name__ == "__main__":

    # --- 利用時に変数を設定してください -------------------------------------------------------
    # コマンド用パラメーター -------------------    
    my_sIssueCode  = ''     # 銘柄コード  '':省略時全銘柄取得
    
    # --- 以上設定項目 -------------------------------------------------------------------------

    # --- ファイル名等を設定（実行ファイルと同じディレクトリ） ---------------------------------------
    fname_account_info = "e_api_account_info.txt"
    fname_login_response = "e_api_login_response.txt"
    fname_info_p_no = "e_api_info_p_no.txt"
    # --- 以上ファイル名設定 -------------------------------------------------------------------------

    my_account_property = class_def_account_property()
    my_login_property = class_def_login_property()
    
    # 口座情報をファイルから読み込む。
    func_get_acconut_info(fname_account_info, my_account_property)
    
    # ログイン応答を保存した「e_api_login_response.txt」から、仮想URLと課税flgを取得
    func_get_login_info(fname_login_response, my_login_property)

    
    my_login_property.sJsonOfmt = my_account_property.sJsonOfmt                   # 返り値の表示形式指定
    my_login_property.sSecondPassword = func_replace_urlecnode(my_account_property.sSecondPassword)        # 22.第二パスワード  APIでは第2暗証番号を省略できない。 関連資料:「立花証券・e支店・API、インターフェース概要」の「3-2.ログイン、ログアウト」参照
    
    # 現在（前回利用した）のp_noをファイルから取得する
    func_get_p_no(fname_info_p_no, my_login_property)
    my_login_property.p_no = my_login_property.p_no + 1
    
    print()
    print('-- 信用建玉一覧 取得 -------------------------------------------------------------')
    dic_return = func_get_shinyou_tategyoku_list(my_login_property.p_no ,
                                                my_sIssueCode,
                                                my_login_property)
    # 送信項目、戻り値の解説は、マニュアル「立花証券・ｅ支店・ＡＰＩ（ｖ〇）、REQUEST I/F、機能毎引数項目仕様」
    # p10/46 No.9 CLMShinyouTategyokuList を参照してください

    print(' 1  メッセージＩＤ:\t', dic_return.get('sCLMID'))
    print(' 2  銘柄コード:\t', dic_return.get('sIssueCode'))
    print(' 3  結果コード:\t', dic_return.get('sResultCode'))
    print(' 4  結果テキスト:\t', dic_return.get('sResultText'))
    print(' 5  警告コード:\t', dic_return.get('sWarningCode'))
    print(' 6  警告テキスト:\t', dic_return.get('sWarningText'))
    print(' 7  売建代金合計:\t', dic_return.get('sUritateDaikin'))
    print(' 8  買建代金合計:\t', dic_return.get('sKaitateDaikin'))
    print(' 9  総代金合計:\t', dic_return.get('sTotalDaikin'))
    print('10  評価損益合計_売建:\t', dic_return.get('sHyoukaSonekiGoukeiUridate'))
    print('11  評価損益合計_買建:\t', dic_return.get('sHyoukaSonekiGoukeiKaidate'))
    print('12  総評価損益合計:\t', dic_return.get('sTotalHyoukaSonekiGoukei'))
    print('13  特定口座残高評価損益合計:\t', dic_return.get('sTokuteiHyoukaSonekiGoukei'))
    print('14  一般口座残高評価損益合計:\t', dic_return.get('sIppanHyoukaSonekiGoukei'))
    print()
    print()
    
    print('==========================')
    list_aShinyouTategyokuList = dic_return.get("aShinyouTategyokuList")
    print('15 信用建玉リスト:  aShinyouTategyokuList')
    print('件数:', len(list_aShinyouTategyokuList))
    print()
    # 'aShinyouTategyokuList'の返値の処理。
    # データ形式は、"aShinyouTategyokuList":[{...},{...}, ... ,{...}]
    for i in range(len(list_aShinyouTategyokuList)):
        print('No.', i+1, '---------------')
        print('16-1 警告コード:\t', list_aShinyouTategyokuList[i].get('sOrderWarningCode'))
        print('17-2 警告テキスト:\t', list_aShinyouTategyokuList[i].get('sOrderWarningText'))
        print('18-3 建玉番号:\t', list_aShinyouTategyokuList[i].get('sOrderTategyokuNumber'))
        print('19-4 銘柄コード:\t', list_aShinyouTategyokuList[i].get('sOrderIssueCode'))
        print('20-5 市場:\t', list_aShinyouTategyokuList[i].get('sOrderSizyouC'))
        print('21-6 売買区分:\t', list_aShinyouTategyokuList[i].get('sOrderBaibaiKubun'))
        print('22-7 弁済区分:\t', list_aShinyouTategyokuList[i].get('sOrderBensaiKubun'))
        print('23-8 譲渡益課税区分:\t', list_aShinyouTategyokuList[i].get('sOrderZyoutoekiKazeiC'))
        print('24-9 建株数:\t', list_aShinyouTategyokuList[i].get('sOrderTategyokuSuryou'))
        print('25-10 建単価:\t', list_aShinyouTategyokuList[i].get('sOrderTategyokuTanka'))
        print('26-11 評価単価:\t', list_aShinyouTategyokuList[i].get('sOrderHyoukaTanka'))
        print('27-12 評価損益:\t', list_aShinyouTategyokuList[i].get('sOrderGaisanHyoukaSoneki'))
        print('28-13 評価損益率:\t', list_aShinyouTategyokuList[i].get('sOrderGaisanHyoukaSonekiRitu'))
        print('29-14 建玉代金:\t', list_aShinyouTategyokuList[i].get('sTategyokuDaikin'))
        print('30-15 建手数料:\t', list_aShinyouTategyokuList[i].get('sOrderTateTesuryou'))
        print('31-16 順日歩:\t', list_aShinyouTategyokuList[i].get('sOrderZyunHibu'))
        print('32-17 逆日歩:\t', list_aShinyouTategyokuList[i].get('sOrderGyakuhibu'))
        print('33-18 書換料:\t', list_aShinyouTategyokuList[i].get('sOrderKakikaeryou'))
        print('34-19 管理費:\t', list_aShinyouTategyokuList[i].get('sOrderKanrihi'))
        print('35-20 貸株料:\t', list_aShinyouTategyokuList[i].get('sOrderKasikaburyou'))
        print('36-21 その他:\t', list_aShinyouTategyokuList[i].get('sOrderSonota'))
        print('37-22 建日:\t', list_aShinyouTategyokuList[i].get('sOrderTategyokuDay'))
        print('38-23 建玉期日日:\t', list_aShinyouTategyokuList[i].get('sOrderTategyokuKizituDay'))
        print('39-24 建玉数量:\t', list_aShinyouTategyokuList[i].get('sTategyokuSuryou'))
        print('40-25 約定返済株数:\t', list_aShinyouTategyokuList[i].get('sOrderYakuzyouHensaiKabusu'))
        print('41-26 現引現渡株数:\t', list_aShinyouTategyokuList[i].get('sOrderGenbikiGenwatasiKabusu'))
        print('42-27 注文中数量:\t', list_aShinyouTategyokuList[i].get('sOrderOrderSuryou'))
        print('43-28 返済可能数量:\t', list_aShinyouTategyokuList[i].get('sOrderHensaiKanouSuryou'))
        print('44-29 前日終値:\t', list_aShinyouTategyokuList[i].get('sSyuzituOwarine'))
        print('45-30 前日比:\t', list_aShinyouTategyokuList[i].get('sZenzituHi'))
        print('46-31 前日比():\t', list_aShinyouTategyokuList[i].get('sZenzituHiPer'))
        print('47-32 騰落率Flag:\t', list_aShinyouTategyokuList[i].get('sUpDownFlag'))
        print()
        print()
    
        
            
    print()
    print('p_errno', dic_return.get('p_errno'))
    print('p_err', dic_return.get('p_err'))
    # 仮想URLが無効になっている場合
    if dic_return.get('p_errno') == '2':
        print()    
        print("仮想URLが有効ではありません。")
        print("電話認証 + e_api_login_tel.py実行")
        print("を再度行い、新しく仮想URL（1日券）を取得してください。")

    print()    
    print()    
    # "p_no"を保存する。
    func_save_p_no(fname_info_p_no, my_login_property.p_no)

