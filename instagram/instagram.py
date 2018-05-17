import utils
import urllib
import hashlib
import hmac
import requests
import json
import logging


class Instagram:
    API_URL = 'https://i.instagram.com/api/v1/'
    USER_AGENT = 'Instagram 8.2.0 Android (18/4.3; 320dpi; 720x1280; Xiaomi; HM 1SW; armani; qcom; en_US)'
    IG_SIG_KEY = '55e91155636eaa89ba5ed619eb4645a4daf1103f2161dbfe6fd94d5ea7716095'
    EXPERIMENTS = 'ig_android_progressive_jpeg,ig_creation_growth_holdout,ig_android_report_and_hide,ig_android_new_browser,ig_android_enable_share_to_whatsapp,ig_android_direct_drawing_in_quick_cam_universe,ig_android_huawei_app_badging,ig_android_universe_video_production,ig_android_asus_app_badging,ig_android_direct_plus_button,ig_android_ads_heatmap_overlay_universe,ig_android_http_stack_experiment_2016,ig_android_infinite_scrolling,ig_fbns_blocked,ig_android_white_out_universe,ig_android_full_people_card_in_user_list,ig_android_post_auto_retry_v7_21,ig_fbns_push,ig_android_feed_pill,ig_android_profile_link_iab,ig_explore_v3_us_holdout,ig_android_histogram_reporter,ig_android_anrwatchdog,ig_android_search_client_matching,ig_android_high_res_upload_2,ig_android_new_browser_pre_kitkat,ig_android_2fac,ig_android_grid_video_icon,ig_android_white_camera_universe,ig_android_disable_chroma_subsampling,ig_android_share_spinner,ig_android_explore_people_feed_icon,ig_explore_v3_android_universe,ig_android_media_favorites,ig_android_nux_holdout,ig_android_search_null_state,ig_android_react_native_notification_setting,ig_android_ads_indicator_change_universe,ig_android_video_loading_behavior,ig_android_black_camera_tab,liger_instagram_android_univ,ig_explore_v3_internal,ig_android_direct_emoji_picker,ig_android_prefetch_explore_delay_time,ig_android_business_insights_qe,ig_android_direct_media_size,ig_android_enable_client_share,ig_android_promoted_posts,ig_android_app_badging_holdout,ig_android_ads_cta_universe,ig_android_mini_inbox_2,ig_android_feed_reshare_button_nux,ig_android_boomerang_feed_attribution,ig_android_fbinvite_qe,ig_fbns_shared,ig_android_direct_full_width_media,ig_android_hscroll_profile_chaining,ig_android_feed_unit_footer,ig_android_media_tighten_space,ig_android_private_follow_request,ig_android_inline_gallery_backoff_hours_universe,ig_android_direct_thread_ui_rewrite,ig_android_rendering_controls,ig_android_ads_full_width_cta_universe,ig_video_max_duration_qe_preuniverse,ig_android_prefetch_explore_expire_time,ig_timestamp_public_test,ig_android_profile,ig_android_dv2_consistent_http_realtime_response,ig_android_enable_share_to_messenger,ig_explore_v3,ig_ranking_following,ig_android_pending_request_search_bar,ig_android_feed_ufi_redesign,ig_android_video_pause_logging_fix,ig_android_default_folder_to_camera,ig_android_video_stitching_7_23,ig_android_profanity_filter,ig_android_business_profile_qe,ig_android_search,ig_android_boomerang_entry,ig_android_inline_gallery_universe,ig_android_ads_overlay_design_universe,ig_android_options_app_invite,ig_android_view_count_decouple_likes_universe,ig_android_periodic_analytics_upload_v2,ig_android_feed_unit_hscroll_auto_advance,ig_peek_profile_photo_universe,ig_android_ads_holdout_universe,ig_android_prefetch_explore,ig_android_direct_bubble_icon,ig_video_use_sve_universe,ig_android_inline_gallery_no_backoff_on_launch_universe,ig_android_image_cache_multi_queue,ig_android_camera_nux,ig_android_immersive_viewer,ig_android_dense_feed_unit_cards,ig_android_sqlite_dev,ig_android_exoplayer,ig_android_add_to_last_post,ig_android_direct_public_threads,ig_android_prefetch_venue_in_composer,ig_android_bigger_share_button,ig_android_dv2_realtime_private_share,ig_android_non_square_first,ig_android_video_interleaved_v2,ig_android_follow_search_bar,ig_android_last_edits,ig_android_video_download_logging,ig_android_ads_loop_count_universe,ig_android_swipeable_filters_blacklist,ig_android_boomerang_layout_white_out_universe,ig_android_ads_carousel_multi_row_universe,ig_android_mentions_invite_v2,ig_android_direct_mention_qe,ig_android_following_follower_social_context'
    SIG_KEY_VERSION = '4'

    def __init__(self, username, password, debug_mode=False):
        self.username = username
        self.password = password
        self.device_id = utils.generate_device_id(utils.md5_sum(username + password))
        self.uuid = utils.generate_uuid(True)
        self.s = requests.Session()
        self.token = ""
        self.rank_token = ""
        self.username_id = ""
        self.phone_id = utils.generate_uuid(True)
        self.csrf_token = ""
        self.debug_mode = debug_mode

    def login(self):
        resp = self.send_request('si/fetch_headers/?challenge_type=signup&guid=' + utils.generate_uuid(), None)
        if resp.status_code != 200:
            return False

        data = {'phone_id': self.phone_id,
                '_csrftoken': resp.cookies['csrftoken'],
                'username': self.username,
                'guid': self.uuid,
                'device_id': self.device_id,
                'password': self.password,
                'login_attempt_count': '0'}

        resp = self.send_request('accounts/login/', self.generate_signature(json.dumps(data)))
        if resp.status_code != 200:
            return False

        resp_json = utils.resp_to_json(resp)
        self.username_id = resp_json["logged_in_user"]["pk"]
        self.rank_token = "%s_%s" % (self.username_id, self.uuid)
        self.token = resp.cookies["csrftoken"]
        return True

    def send_request(self, endpoint, post=None):
        if self.debug_mode:
            logging.info('Sending request to {} , post={}'.format(endpoint, post))

        self.s.headers.update({'Connection': 'close',
                               'Accept': '*/*',
                               'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'User-Agent': self.USER_AGENT})

        if post is not None:
            response = self.s.post(self.API_URL + endpoint, data=post)
        else:
            response = self.s.get(self.API_URL + endpoint)

        if self.debug_mode:
            logging.info('Response is ' + response.content)

        return response

    def logout(self):
        self.send_request('accounts/logout/')

    def direct_list(self, next_page=''):
        uri = 'direct_v2/inbox/'
        if next_page:
            uri += '?cursor=' + next_page

        resp = self.send_request(uri)
        if resp.status_code != 200:
            return False

        resp_json = utils.resp_to_json(resp)
        return resp_json

    def direct_thread(self, thread, next_page=''):
        uri = 'direct_v2/threads/{}/'.format(thread)
        if next_page:
            uri += '?cursor=' + next_page

        resp = self.send_request(uri)
        if resp.status_code != 200:
            return False

        resp_json = utils.resp_to_json(resp)
        return resp_json

    def generate_signature(self, data):
        return 'ig_sig_key_version=' + self.SIG_KEY_VERSION + '&signed_body=' + hmac.new(
            self.IG_SIG_KEY.encode('utf-8'), data.encode('utf-8'),
            hashlib.sha256).hexdigest() + '.' + urllib.quote_plus(data)
