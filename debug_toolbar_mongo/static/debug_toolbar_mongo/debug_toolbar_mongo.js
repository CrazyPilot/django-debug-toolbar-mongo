import { $$ } from "../debug_toolbar/js/utils.js";

let mongoExplain = (e) => {
    let target = e.target
    let query = window.djdtMongoQueries[target.dataset.queryIdx]
    console.log(query)
}

function onRender() {
    // Be sure to cover the case of this function being called twice
    // due to file being loaded asynchronously.
    if(window.djdtMongoQueries === undefined){
        // Эта штука выполнится один раз
        for( let i of document.querySelectorAll('.djdt-mongo-btn-explain')){
            i.addEventListener('click', mongoExplain)
        }
        window.djdtMongoQueries = JSON.parse(document.getElementById('djdt-mongo-json-queries').textContent)
    }
}
const djDebug = document.getElementById("djDebug");
$$.onPanelRender(djDebug, "MongoPanel", onRender);
// Since a panel's scripts are loaded asynchronously, it's possible that
// the above statement would occur after the djdt.panel.render event has
// been raised. To account for that, the rendering function should be
// called here as well.
onRender();