# -*- coding: utf-8 -*-
# Copyright (c) 2026 Tachibana Securities Co., Ltd. All rights reserved.

# 2021.07.08,   yo.
# 2022.10.25 reviced,   yo.
# 2025.07.27 reviced,   yo.
# 2026.06.21 reviced,   yo.
#
# 立花証券ｅ支店ＡＰＩ利用のサンプルコード
#
# 動作確認
# Python 3.13.5 / debian13
# API v4r9
#
# 利用方法: 
# 事前に「e_api_login_pubkey.py」を実行して、仮想URL等を取得しておいてください。
# 実行は「e_api_login_pubkey.py」と同じディレクトリで行ってください。
#
# ------------------------------------------------------------------
#
# APIの基本設計について
# 
# 本APIは、プログラミング初心者や非ITエンジニアの方にも
# 利用しやすいよう、URLにJSON形式のパラメーターを付加して
# 送信する独自方式を採用しています。
# 
# 一般的なWeb APIとは異なる構成ですが、
# HTTPヘッダーやPOSTデータなどの知識を最小限に
# 抑えながら利用できることを重視しています。
# 
# このため、本APIは、URLとJSON文字列を組み立てて
# 送信するだけで利用でき、特別な知識を必要とせず、
# 各種スクリプト言語からも実装しやすいことを
# 優先した設計となっています。
#  
# ------------------------------------------------------------------
# 
# 機能: 信用建玉一覧の取得
#
# == ご注意: ========================================
#   本番環境にに接続した場合、実際に市場に注文が出ます。
#   市場で約定した場合取り消せません。
# ==================================================
#

import urllib3
import datetime
import json
import os
import urllib.parse
from zoneinfo import ZoneInfo

# =========================================================================
# --- 設定項目（定数定義） ---
# =========================================================================
# コマンド用パラメーター -------------------    
S_ISSUE_CODE = ''   # 銘柄コード  '':省略時全銘柄取得

# --- 共通設定項目 ------------------------------------------------------------
FNAME_URL_INFO = "file_url_info.txt"                # API接続情報ファイル
FNAME_PASSWD2 = "./.auth/file_pwd2.txt"              # 第二パスワード保存ファイル
FNAME_LOGIN_RESPONSE = "./.auth/file_login_response.txt"  # ログイン応答保存先
FNAME_INFO_P_NO = "file_info_p_no.txt"              # p_no保存ファイル

# --- 通信堅牢化のための設定項目 ---
API_TIMEOUT_SECONDS = 15.0  # タイムアウト時間（秒）: 応答がない場合15秒で切り上げる
MAX_RETRY_COUNT = 3         # 最大リトライ回数: 通信エラー時に自動再試行する回数
RETRY_INTERVAL_SECONDS = 5  # リトライ間隔（秒）: 再試行する前に待機する時間
# =========================================================================


# --- 共通ユーティリティ関数 ----------------------------------------------

def func_p_sd_date():
    """
    機能: システム時刻を"p_sd_date"の書式の文字列で返す。
    返値: "p_sd_date"の書式の文字列。 API規定書式 "YYYY.MM.DD-hh:mm:ss.sss"
    引数1: なし
    備考: 
        日本標準時（Japan Standard Time、JST）を利用のこと。
    """
    dt_now = datetime.datetime.now(
        # 日本標準時（Japan Standard Time、JST）を利用
        ZoneInfo("Asia/Tokyo")
    )
    # 年.月.日-時:分:秒 の部分を作成
    str_date = dt_now.strftime("%Y.%m.%d-%H:%M:%S")
    
    # マイクロ秒（6桁ゼロ埋め）から先頭の3桁を切り出してミリ秒を作成
    str_micro = f"{dt_now.microsecond:06d}"
    str_ms = str_micro[0:3]
    
    # ドットで結合してAPI規定書式を完成
    return str_date + "." + str_ms


def func_replace_urlencode(str_input):
    """
    URLエンコードを行う。

    URLでは、スペースや「&」「+」「?」などの記号が
    特別な意味を持つため、そのまま送信できない場合がある。
    そのため、これらの文字を「%xx」形式へ変換する。

    例:
        "A B+C" → "A%20B%2BC"

    本サンプルでは Python標準ライブラリの
    urllib.parse.quote() を利用してURLエンコードを行う。

    他言語へ移植する場合も、自前で変換処理を作成するのではなく、
    各言語が提供する標準のURLエンコード関数を利用することを推奨する。

    主な対応例:
        Python      : urllib.parse.quote()
        Java        : java.net.URLEncoder.encode()
        C#          : Uri.EscapeDataString()
        JavaScript  : encodeURIComponent()
        Go          : url.QueryEscape()

    Parameters
    ----------
    str_input : str
        URLエンコード対象文字列

    Returns
    -------
    str
        URLエンコード後の文字列
    """
    return urllib.parse.quote(str_input, safe='')


def func_read_from_file(str_fname):
    """ファイルから文字情報を一括読み込み（BOMを排除）"""
    str_read = ''
    try:
        # utf-8-sig を指定してBOMを自動的に排除しファイルを開く
        with open(str_fname, 'r', encoding='utf-8-sig') as fin:
            while True:
                line = fin.readline()
                if not line:
                    break
                str_read = str_read + line
        return str_read
    except IOError as e:
        print(f"[エラー] ファイルを読み込めません: {str_fname}")
        raise e


def func_write_to_file(str_fname_output, str_data):
    """ファイルに書き込み、権限を所有者のみ(600)に制限"""
    try:
        # 出力先フォルダの存在を確認し、存在しない場合は自動作成
        str_dir = os.path.dirname(str_fname_output)
        if str_dir and not os.path.exists(str_dir):
            os.makedirs(str_dir, exist_ok=True)

        # データをファイルへ書き込み
        with open(str_fname_output, 'w', encoding='utf-8') as fout:
            fout.write(str_data)
        
        # パーミッションを600（所有者のみ読み書き可能）に制限
        os.chmod(str_fname_output, 0o600)
    except IOError as e:
        print(f"[エラー] ファイルに書き込めません: {str_fname_output}")
        raise e


def func_get_url_info(fname):
    """
    file_url_info.txt からAPI接続設定を取得

    機能: API接続情報をファイルから取得し辞書型で返す
    引数1: 接続先情報を保存したファイル名: fname_url_info

    サポートへの問い合わせは、sJsonOfmt:'5'でお願いします。
    """
    str_url_info = func_read_from_file(fname)
    # JSON形式の文字列を辞書型で取り出す
    return  json.loads(str_url_info)    


def func_get_login_response(str_fname):
    '''
    ログインレスポンスを取得
    '''
    str_login_response = func_read_from_file(str_fname)
    dic_login_response = json.loads(str_login_response)
    return dic_login_response
    

def func_get_p_no(fname):
    """ 
    機能: p_noをファイルから取得する
    引数1: p_noを保存したファイル名（fname_info_p_no = "e_api_info_p_no.txt"）
    """
    str_p_no_info = func_read_from_file(fname)
    # JSON形式の文字列を辞書型で取り出す
    json_p_no_info = json.loads(str_p_no_info)
    int_p_no = int(json_p_no_info.get('p_no'))
    return int_p_no


def func_save_p_no(str_fname_output, int_p_no):
    """p_noを保存するためのJSONファイルを生成"""
    p_no_dict = {"p_no": str(int_p_no)}
    json_data = json.dumps(p_no_dict, indent=4)
    func_write_to_file(str_fname_output, json_data)
    print(f'現在の "p_no" を保存しました。 p_no = {int_p_no} -> {str_fname_output}')


def func_make_url_request_from_dic(
                                    auth_flg,       # ログインFlag。    login:true   login以外:false
                                    url_target,     # 接続先URL
                                    work_dic_req    # API要求項目
):
    '''
    API問合せ用完全URL（クエリパラメータ付）を作成
    
    ------------------------------------------------------------------

    APIの基本設計について

    本APIは、プログラミング初心者や非ITエンジニアの方にも
    利用しやすいよう、URLにJSON形式のパラメーターを付加して
    送信する独自方式を採用しています。

    一般的なWeb APIとは異なる構成ですが、
    HTTPヘッダーやPOSTデータなどの知識を最小限に
    抑えながら利用できることを重視しています。

    このため、本APIは、URLとJSON文字列を組み立てて
    送信するだけで利用でき、特別な知識を必要とせず、
    各種スクリプト言語からも実装しやすいことを
    優先した設計となっています。
    
    ------------------------------------------------------------------
    JSONをHTTPボディではなくURLに付加して送信します。
    詳細はAPIマニュアル参照。
    備考：
        サポートへの問い合わせを考慮し、項目ごとの改行とタブを入れてあります。
    '''
    str_url = url_target
    if auth_flg:
        str_url = urllib.parse.urljoin(str_url, 'auth/')
    json_param = json.dumps(work_dic_req, indent=4, ensure_ascii=False)
    return f"{str_url}?{json_param}"


def func_api_req(str_request_method, str_url): 
    """
    APIリクエストの送信と、Shift-JIS応答のデコード（リトライ・タイムアウト対応版）
    """
    # HTTP通信ライブラリ urllib3 を利用します。
    #
    # requests ライブラリでも同様の処理は可能ですが、
    # 本サンプルでは APIサーバーへの接続処理が分かりやすいよう、
    # より基本的な urllib3 を利用しています。
    #
    # 他言語へ移植する場合も、
    # 「HTTPクライアント生成 → リクエスト送信 → レスポンス受信」
    # の流れを対応するライブラリへ置き換えてください。

    print('--- 送信電文 -------------------------------------------')
    print(str_url)

    # 接続および読み込みのタイムアウト時間を設定
    timeout_config = urllib3.Timeout(connect=API_TIMEOUT_SECONDS, read=API_TIMEOUT_SECONDS)
    http = urllib3.PoolManager()
    
    response_data = None
    status_code = None

    # 最大試行回数に達するまで通信をリトライ
    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            # 2回目以降の試行（再接続）の前に、指定されたインターバル時間待機
            if attempt > 1:
                print(f"[{attempt}/{MAX_RETRY_COUNT} 回目] 再接続を試みます...（{RETRY_INTERVAL_SECONDS}秒待機）")
                time.sleep(RETRY_INTERVAL_SECONDS)

            req = http.request(str_request_method, str_url, timeout=timeout_config)
            status_code = req.status
            response_data = req.data
            break  # 正常に通信できた場合はループを抜ける

        except (TimeoutError, MaxRetryError) as ce:
            print(f"\n[警告] 通信エラーが発生しました (試行: {attempt}/{MAX_RETRY_COUNT})")
            print(f"エラー詳細: {ce}")
            
            # 最大リトライ回数を超えて失敗した場合はConnectionErrorを発生
            if attempt == MAX_RETRY_COUNT:
                raise ConnectionError(
                    f"APIサーバーへの接続に規定回数失敗しました。サーバーがメンテナンス中か、停止している可能性があります。\n"
                    f"設定されたタイムアウト時間: {API_TIMEOUT_SECONDS}秒"
                )
        except Exception as ex:
            print(f"\n[警告] 予期せぬネットワーク例外が発生しました: {ex}")
            if attempt == MAX_RETRY_COUNT:
                raise ex

    print(f"HTTP Status: {status_code}")

    # 受信した電文をShift-JISからUTF-8へデコード（不正なバイトは無視）
    str_response = response_data.decode("shift-jis", errors="ignore")
    print('--- 受信電文 -------------------------------------------')
    print(str_response)
    print('--------------------------------------------------------')

    return str_response


def func_api_request_from_dic(
                                flg_login,          # ログインFlag。    login:true   login以外:false
                                destination_url,    # 接続先URL。
                                                    #   ログイン時は、FNAME_URL_INFOから取得する接続先。
                                                    #   それ以外はログインレスポンスで指定される仮想URL。
                                dic_req_item        # API要求項目
):
    '''
    APIへの問い合わせを実行する。
    '''
    # URL文字列の作成
    str_url = func_make_url_request_from_dic(
                                                flg_login,          # ログインFlag。    login:true   login以外:false
                                                destination_url,    # 接続先URL
                                                dic_req_item        # API要求項目
    )

    # APIへの問い合わせ。
    # リクエストメソッドの指定('GET'、'POST'どちらでも動作します。)
    str_api_response = func_api_req('POST', str_url)

    # apiの返り値（JSON形式の文字列）を辞書型で取り出す
    dic_api_response = json.loads(str_api_response)
    
    return dic_api_response

# --- 共通ユーティリティ関数 ----------------------------------------------


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
# --- 以上参考資料 ---------------------

# ======================================================================================================
#     プログラム始点 
# ======================================================================================================

if __name__ == "__main__":

    # 表示形式を接続情報ファイルから読み込む。
    dic_url_info = func_get_url_info(FNAME_URL_INFO)
    str_sJsonOfmt = dic_url_info.get("sJsonOfmt")

    # ログイン応答を保存した「file_login_response.txt」から、仮想URLと口座情報を取得
    dic_login_property = func_get_login_response(FNAME_LOGIN_RESPONSE)

    # 現在（前回利用した）のp_noをファイルから取得する
    my_p_no = func_get_p_no(FNAME_INFO_P_NO)
    my_p_no = my_p_no + 1
    # 更新した"p_no"を保存する。
    func_save_p_no(FNAME_INFO_P_NO, my_p_no)
    
    print()
    print('-- 信用建玉一覧 取得 -------------------------------------------------------------')
    # API要求項目のセット
    dic_req_item = {
        'p_no':                 str(my_p_no),
        'p_sd_date':            func_p_sd_date(),
        'sCLMID':               'CLMShinyouTategyokuList',      # 信用建玉一覧取得
        'sIssueCode':           S_ISSUE_CODE,                   # 銘柄コード（6501等、'':省略時全銘柄取得）。
        'sJsonOfmt':            str_sJsonOfmt                   # 表示形式（サポートへの問い合わせでは'5'を指定指定した送信電文と受信電文で。）
    }

    # 'CLMShinyouTategyokuList'は、仮想URL:'sUrlRequest'
    str_connection_url = dic_login_property.get('sUrlRequest')
    # API問い合わせ実行
    dic_return = func_api_request_from_dic(
                                                False,                  # ログインFlag。    login:true   login以外:false
                                                str_connection_url,     # 接続先URL。
                                                                        #    ログイン時は、FNAME_URL_INFOから取得する接続先。
                                                                        #   それ以外はログインレスポンスで指定される仮想URL。
                                                dic_req_item            # API要求項目
                                            )

if dic_return is None:
        print('API接続自体の失敗')
        print('JSON形式の受信電文ではありません。接続先も含めて送信電文、受信電文を確認してください。')
else:
    if dic_return.get('p_errno') != '-2' and dic_return.get('p_errno') != '2':
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
        
    elif dic_return.get('p_errno') == '-2' :
        print()
        print('p_errno', dic_return.get('p_errno'))
        print('p_err', dic_return.get('p_err'))
        print("パラメーターの設定に誤りが有ります。")

    # 仮想URLが無効になっている場合
    # if dic_return.get('p_errno') == '2':
    else:
        print()
        print('p_errno', dic_return.get('p_errno'))
        print('p_err', dic_return.get('p_err'))
        print("仮想URLが有効ではありません。")
        print("e_api_login_pubkey.py")
        print("の実行を再度行い、新しく仮想URL（1日券）を取得してください。")
        
    print()    
    print()
    # 最終の'p_no'を保存する。
    func_save_p_no(FNAME_INFO_P_NO, my_p_no)