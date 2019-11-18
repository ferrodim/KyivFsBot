

function MongoService(){
    this._db = null;
    this.ready = new Promise((accept, reject) =>  {
        this.configure = function(args){
            require('mongodb').MongoClient.connect(process.env.MONGO_URL, {useUnifiedTopology: true}, (err, client) => {
                console.log("Connected successfully to db server");
                this._db = client.db();
                accept();
            });

            return this.ready;
        };
    });
}

MongoService.prototype.collection = function(name){
    return this._db.collection(name);
};


module.exports = {
    mongo: new MongoService()
};