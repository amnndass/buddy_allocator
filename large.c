#include <stdio.h>
#include <limits.h> 

int findLarge(int arr[], int n) {
    int large = arr[0]; 
    for(int i = 1; i < n; i++) {
        if(arr[i] > large){
            large = arr[i];
        }
    }
    return large;
}

int main() {
    int n, arr[50], i;

    printf("enter numebr of elements: ");
    scanf("%d", &n);

    for(i = 0; i<n; i++) {
        scanf("%d", &arr[i]);
    }

    int large = findLarge(arr,n);

    printf("largest number is %d", large);
}