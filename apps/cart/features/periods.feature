Feature: Testing periods

    Scenario: Fill database
        Given I have the following users in my database:
            | username     | email                 | first_name | last_name  |
            | Anton        | anton@gmail.com       | Anton      | Romanovich |
        
        Given I have the following stores in my database:
            | name         | user  | category    |
            | Cool Store   | Anton | Test Stores |
        
        Given I have the following discount models in "Cool Store":
            | name           | for_additional_item | for_additional_buyer | lower_bound |
            | DiscountModel1 | 5                   | 5                    | 50          |

        Given I have the following items in "Cool Store" grouped together with "DiscountModel1":
            | name         | price  |
            | iPad         | 400.00 |
            | iPhone       | 200.00 |

   Scenario: Expire Social Buy
        Given I'm logged in as Anton.
        
        Given To buy 1 "iPad" I create a Social Buy that finishes in 1 hours. Let's call it Buy1.
        Then I see the only following Social Buys:
            | name |
            | Buy1 |

        Given It's 2 hours later.
        Then I see no Social Buys.
        But I don't see any Social Buy on "iPad" item page.

    Scenario: Expire pending Shipping Request
        Given It's 0 hours later.
        And I request shipping for Buy1.
        
        Then I see pending Shipping Requests only for the following Social Buys:
            | name |
            | Buy1 |
         
        Given It's 2 hours later.
        But I see pending Shipping Requests only for the following Social Buys:
            | name |
            | Buy1 |
        
        Given It's 5 hours later.
        And I see no pending Shipping Requests.

        Given It's 2 hours later.
        And I cancel pending Shipping Request for Buy1.
        Then I see totally empty cart.

    Scenario: Expire Shipping Request
        Given It's 0 hours later.
        And I request shipping for Buy1.

        Given It's 2 hours later.
        And Seller respond to Shipping Request for Buy1 and assign price 12.00.
        Then I see Shipping Requests only for the following Social Buys:
            | name |
            | Buy1 |

        Given It's 5 hours later.
        Then I see Shipping Requests only for the following Social Buys:
            | name |
            | Buy1 |
        
        Given It's 7 hours later.
        Then I see totally empty cart.

        Given It's 5 hours later.
        And I cancel pending Shipping Request for Buy1.
        Then I see totally empty cart.
