import Cookies from 'universal-cookie';

// return the token from the session storage
export const getToken = () => {
	const cookies = new Cookies();
	const usertoken = cookies.get('session_token')
    const userid = cookies.get('session_userid')
  	return (usertoken && userid) ? true : false;
}