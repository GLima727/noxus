# Stops all containers, Removes all containers, Deletes all database data
docker compose down --volumes

# builds app
docker compose up --build


# Run the db container
docker exec -it noxus-db-1 psql -U postgres -d noxus


i decided to use groq as it dlawodaw

i decided to not use sqlite evne tough i am more used to it because bla i wanna leanr bla bla postgres bla

