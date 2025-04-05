# Stops all containers, Removes all containers, Deletes all database data
docker compose down --volumes

# builds app
docker compose up --build


# Run the db container
docker exec -it noxus-db-1 psql -U postgres -d noxus