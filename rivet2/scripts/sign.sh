#!/bin/bash -e

release_dir=$1
passphrase_file=$HOME/PASSPHRASE

function cleanup {
    rm -f $passphrase_file
}

trap cleanup EXIT

read -ers -p "Passphrase: " passphrase

echo "$passphrase" > "$passphrase_file"

cd "$release_dir"

for file in $(find . | egrep 'gz$'); do
    gpg2 --sign --armor --detach --default-key="CODE SIGNING KEY" --passphrase-file "$passphrase_file" "$file"
done
