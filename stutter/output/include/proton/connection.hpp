namespace proton {

class connection {
  public:
    connection() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}