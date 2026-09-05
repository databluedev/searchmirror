import React from 'react';
import { Route, Redirect } from 'react-router-dom';
import { getToken } from './common';

// handle the public routes
function PublicRoute({ component: Component, ...rest }) { 
	return (
	  	<>
	  		{!getToken() ?
	    		<Route {...rest} render={ (props) => <Component {...props} /> } />
	  		: 
	  			<Redirect to={{ pathname: '/projects' }} /> 
	  		} 
	    </>
	)
}

export default PublicRoute; 