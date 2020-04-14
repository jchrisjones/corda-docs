import CookiesEuBanner from 'cookies-eu-banner';

export function cookieBanner() {
	new CookiesEuBanner(function () {
		console.log('wibble');
	}, true)
}