function isTeamAccount(fullbasedata) {
   return fullbasedata?.ac_typ === "team";
}

export function allowsTeamModule(fullbasedata, module) {
   if (!isTeamAccount(fullbasedata)) return true;
   const modules = fullbasedata?.team_modules || {};
   return Object.prototype.hasOwnProperty.call(modules, module);
}

export function allowsTeamAction(fullbasedata, module, action) {
   if (!allowsTeamModule(fullbasedata, module)) return false;
   if (!isTeamAccount(fullbasedata)) return true;
   return (fullbasedata?.team_modules?.[module] || []).includes(action);
}
