import { $$ } from "../debug_toolbar/js/utils.js";

let mongoExplain = (e) => {
    let target = e.target
    let query = window.djdtMongoQueries[target.dataset.queryIdx]
    console.log(query)
}

function onRender() {
    console.log("MongoPanel scripts")

    if(window.djdtMongoQueries === undefined){
        // Эта штука выполнится один раз
        console.log("MongoPanel scripts init")

        for( let i of document.querySelectorAll('.djdt-mongo-btn-explain')){
            i.addEventListener('click', mongoExplain)
        }

        window.djdtMongoQueries = JSON.parse(document.getElementById('djdt-mongo-json-queries').textContent)
    }



    // Be sure to cover the case of this function being called twice
    // due to file being loaded asynchronously.
}
const djDebug = document.getElementById("djDebug");
$$.onPanelRender(djDebug, "MongoPanel", onRender);
// Since a panel's scripts are loaded asynchronously, it's possible that
// the above statement would occur after the djdt.panel.render event has
// been raised. To account for that, the rendering function should be
// called here as well.
onRender();