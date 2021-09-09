# Endpoints

## /beers

### **[POST]** /beers
#### Post Data
```json
{
    "name": str,
    "brewery": int,
    "style": int,
    "sub_style": int,
    "abv": decimal,
    "ibu": int,
    "color": int
}
```
#### Response Data
```json
{
    "id": int,
    "name": str,
    "brewery": int,
    "style": int,
    "sub_style": int,
    "abv": decimal,
    "ibu": int,
    "color": int
}
```

### **[GET]** /beers/{id}
#### Response Data
```json
{
    "id": int,
    "name": str,
    "brewery": int,
    "style": int,
    "sub_style": int,
    "abv": decimal,
    "ibu": int,
    "color": int
}
```


## /breweries

### **[POST]** /breweries
#### Post Data
```json
{
    "name": str,
    "country": int
}
```
#### Response Data
```json
{
    "id": int,
    "name": str,
    "country": int
}
```

### **[GET]** /breweries/{id}
#### Response Data
```json
{
    "id": int,
    "name": str,
    "country": int
}
```


## /colors

### **[GET]** /colors/{id}
#### Response Data
```json
{
    "id": int,
    "name": str,
    "color": str
}
```


## /countries

### **[GET]** /countries/{id}
#### Response Data
```json
{
    "id": int,
    "name": str,
    "flag": str
}
```


## /ratings

### **[GET]** /ratings/{id}
#### Response Data
```json
{
    "id": int,
    "user": int,
    "beer": int,
    "appearance": int,
    "smell": int,
    "taste": int,
    "aftertaste": int,
    "score": int,
    "serving": int,
    "aromas_malty": bool,
    "aromas_hoppy": bool,
    "aromas_yeasty": bool,
    "aromas_earthy": bool,
    "aromas_herbal": bool,
    "aromas_woody": bool,
    "aromas_citrus": bool,
    "aromas_redfruits": bool,
    "aromas_tropicalfruits": bool,
    "aromas_honey": bool,
    "aromas_nut": bool,
    "aromas_spices": bool,
    "aromas_caramel": bool,
    "aromas_chocolate": bool,
    "aromas_coffee": bool,
    "comment": str,
    "date": timestamp
}
```


## /servings

### **[GET]** /servings/{id}
#### Response Data
```json
{
    "id": int,
    "name": str
}
```


## /styles

### **[POST]** /styles
#### Post Data
```json
{
    "name": str,
    "substyle_name": str
}
```
#### Response Data
```json
{
    "id": int,
    "name": str,
    "substyle_id": int,
    "substyle_name": str,
}
```

### **[GET]** /styles/{id}
#### Response Data
```json
[
    {
        "id": int,
        "name": str,
        "substyle_id": int,
        "substyle_name": str,
    },
    ...
]
```

### **[GET]** /styles/{id}/{substyle_id}
#### Response Data
```json
{
    "id": int,
    "name": str,
    "substyle_id": int,
    "substyle_name": str,
}
```



## /users

### **[GET]** /users/{id}
#### Response Data
```json
{
    "id": int,
    "username": str,
    "nationality": int,
    "ratings": int
}
```
