# Endpoints

## /beers

### **[GET]** /beers/{id}
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

### **[GET]** /breweries/{id}
```json
{
    "id": int,
    "name": str,
    "country": int
}
```


## /colors

### **[GET]** /colors/{id}
```json
{
    "id": int,
    "name": str,
    "color": str
}
```


## /countries

### **[GET]** /countries/{id}
```json
{
    "id": int,
    "name": str,
    "flag": str
}
```


## /ratings

### **[GET]** /ratings/{id}
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
```json
{
    "id": int,
    "name": str
}
```


## /styles

### **[GET]** /styles/{id}

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
```json
{
    "id": int,
    "username": str,
    "nationality": int,
    "ratings": int
}
```
