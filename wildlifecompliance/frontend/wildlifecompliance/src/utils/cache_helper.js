import localforage from 'localforage';
import Vue from 'vue';
import { fetch_util } from '@/utils/hooks';
/*
 * Functions below are named after 'Cache' but no cache functionality is used.
 * On the firefox, cache fanctionality doesn't work very well, therefore it has been removed
 */
export default {
    getSetCache: async (store_name, key, url, expiry) => {
        const returnedFromUrl = await fetch_util.fetchUrl(url);
        return returnedFromUrl
    },
    getSetCacheList: async (store_name, url, expiry) => {
        let returned_list = [];  
        const returnedFromUrl = await fetch_util.fetchUrl(url);
        if (returnedFromUrl.results) {
            for (let record of returnedFromUrl.results) {
                returned_list.push(record);
            }
        } else if (returnedFromUrl && returnedFromUrl && returnedFromUrl[0] && returnedFromUrl[0].id) {
            for (let record of returnedFromUrl) {
                returned_list.push(record);
            }
        } else if (returnedFromUrl[0] && returnedFromUrl[0].pk) {
            for (let record of returnedFromUrl) {
                returned_list.push(record);
            }
        }
        return returned_list
    }
};
